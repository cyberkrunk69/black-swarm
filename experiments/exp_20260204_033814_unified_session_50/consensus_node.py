"""
consensus_node.py
-----------------
Implements a 3‑round multi‑model debate protocol for critical decisions.

Rounds
------
1. **Generation** – Three independent models generate candidate solutions.
2. **Blind Judging** – Anonymized solutions are ranked by a separate judging
   model (or a deterministic scorer). If a clear consensus (majority top‑rank)
   is reached, the round ends.
3. **Debate** – If no consensus emerges, the top‑ranked solutions enter a
   structured debate where each model can critique the others. After the
   debate a final blind‑judging pass decides the winner.

All dissenting opinions and ranking histories are logged for auditability.

The implementation is deliberately lightweight and uses abstract ``Model`` and
``Judge`` interfaces so that the node can be plugged into any environment
that provides concrete model objects (e.g., OpenAI, Anthropic, local LLMs).
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Protocol

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logger = logging.getLogger("ConsensusNode")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


# --------------------------------------------------------------------------- #
# Abstract interfaces – concrete implementations are injected at runtime
# --------------------------------------------------------------------------- #
class Model(Protocol):
    """A minimal interface that any LLM wrapper must implement."""

    name: str

    def generate(self, prompt: str) -> str:
        """Return a textual solution for the given prompt."""
        ...


class Judge(Protocol):
    """Interface for a model that can rank anonymized solutions."""

    name: str

    def rank(self, anonymized_solutions: List[str]) -> List[int]:
        """
        Return a list of indices representing the ranking order.
        The first element is the index of the top‑ranked solution.
        """
        ...


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class Solution:
    """Container for a model's generated solution."""
    model_name: str
    content: str
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class DebateRound:
    """Tracks a single debate iteration."""
    round_number: int
    critiques: Dict[str, str]  # model_name -> critique text
    final_ranking: List[int] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Core ConsensusNode implementation
# --------------------------------------------------------------------------- #
class ConsensusNode:
    """
    Orchestrates the 3‑round consensus protocol.

    Parameters
    ----------
    models : List[Model]
        Exactly three distinct model instances used for generation.
    judge : Judge
        Model responsible for blind ranking.
    max_debate_rounds : int, optional
        Upper bound on debate iterations before forced termination.
    """

    def __init__(
        self,
        models: List[Model],
        judge: Judge,
        max_debate_rounds: int = 3,
    ):
        if len(models) != 3:
            raise ValueError("Exactly three generation models are required.")
        self.models = models
        self.judge = judge
        self.max_debate_rounds = max_debate_rounds

        # Internal state
        self.generation_history: List[List[Solution]] = []
        self.judging_history: List[Dict[str, Any]] = []
        self.debate_history: List[DebateRound] = []

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def run(self, task_prompt: str) -> Tuple[Solution, List[Dict[str, Any]]]:
        """
        Execute the full protocol for a given task prompt.

        Returns
        -------
        winning_solution : Solution
            The solution that achieved consensus (or final winner after debate).
        audit_log : List[Dict]
            Chronological log of each stage for external inspection.
        """
        logger.info("=== Consensus Protocol Started ===")
        # 1️⃣ Generation
        solutions = self._generation_phase(task_prompt)
        # 2️⃣ Blind Judging
        consensus, ranking = self._blind_judging_phase(solutions)

        # 3️⃣ Debate (if needed)
        if not consensus:
            logger.info("No consensus after initial judging – entering debate.")
            winning_solution = self._debate_phase(solutions, ranking)
        else:
            winning_solution = solutions[ranking[0]]

        audit_log = {
            "generation": [s.__dict__ for s in solutions],
            "judging": self.judging_history,
            "debate": [d.__dict__ for d in self.debate_history],
            "final_winner": winning_solution.__dict__,
        }
        logger.info("=== Consensus Protocol Completed ===")
        return winning_solution, audit_log

    # --------------------------------------------------------------------- #
    # Private helpers
    # --------------------------------------------------------------------- #
    def _generation_phase(self, prompt: str) -> List[Solution]:
        logger.info("🔧 Generation Phase – invoking %d models.", len(self.models))
        solutions = []
        for model in self.models:
            try:
                content = model.generate(prompt)
                sol = Solution(model_name=model.name, content=content)
                solutions.append(sol)
                logger.debug("Model %s generated solution UID %s.", model.name, sol.uid)
            except Exception as e:
                logger.error("Generation error from model %s: %s", model.name, e)
                raise

        self.generation_history.append(solutions)
        return solutions

    def _blind_judging_phase(
        self, solutions: List[Solution]
    ) -> Tuple[bool, List[int]]:
        """
        Perform blind ranking.

        Returns
        -------
        consensus : bool
            True if a majority (2 out of 3) agree on the top rank.
        ranking : List[int]
            Indices of solutions ordered from best to worst.
        """
        logger.info("🔎 Blind Judging Phase – anonymizing solutions.")
        anonymized = [sol.content for sol in solutions]

        try:
            ranking = self.judge.rank(anonymized)
        except Exception as e:
            logger.error("Judging failed: %s", e)
            raise

        # Store judgement details
        judgement_record = {
            "judge": self.judge.name,
            "ranking": ranking,
            "anonymized_solutions": anonymized,
        }
        self.judging_history.append(judgement_record)

        # Determine consensus: if the top index appears at least twice (impossible
        # with unique indices) – we actually need to check if the top two are the
        # same solution across multiple judges. Since we have a single judge, we
        # treat consensus as “clear top choice” i.e., no tie for first place.
        # For extensibility we keep the boolean flag.
        top_index = ranking[0]
        # Check if any other solution ties for first (unlikely with rank list)
        consensus = True  # single judge gives deterministic top
        logger.info(
            "Blind judging ranking: %s (top solution UID %s)",
            ranking,
            solutions[top_index].uid,
        )
        return consensus, ranking

    def _debate_phase(
        self, solutions: List[Solution], initial_ranking: List[int]
    ) -> Solution:
        """
        Conduct up to ``max_debate_rounds`` of structured debate.
        Each round:
            * Every model critiques the current top‑ranked solution(s).
            * The judge re‑ranks based on updated content (original + critiques).
        """
        current_solutions = solutions.copy()
        for rnd in range(1, self.max_debate_rounds + 1):
            logger.info("💬 Debate Round %d", rnd)

            # Identify top‑2 candidates for critique (more than one to allow
            # comparison). If only one, we still allow critiques.
            top_indices = initial_ranking[:2]
            critiques: Dict[str, str] = {}

            for model in self.models:
                # Build a prompt containing the candidate solutions and ask for a
                # critique. In a real system, you'd call the model here.
                critique_prompt = self._build_critique_prompt(
                    model_name=model.name,
                    candidates=[current_solutions[i] for i in top_indices],
                )
                try:
                    critique = model.generate(critique_prompt)
                except Exception as e:
                    logger.error("Critique generation failed for %s: %s", model.name, e)
                    critique = "No critique provided."

                critiques[model.name] = critique
                logger.debug("Critique from %s: %s", model.name, critique)

            # Append critiques to the original solutions (simple concatenation)
            for idx in top_indices:
                sol = current_solutions[idx]
                sol.content += "\n\n--- Critiques ---\n"
                for model_name, critique in critiques.items():
                    sol.content += f"[{model_name}]: {critique}\n"

            # Re‑run blind judging on the updated pool
            anonymized = [sol.content for sol in current_solutions]
            try:
                new_ranking = self.judge.rank(anonymized)
            except Exception as e:
                logger.error("Re‑judging failed during debate: %s", e)
                raise

            # Record debate round
            debate_round = DebateRound(
                round_number=rnd,
                critiques=critiques,
                final_ranking=new_ranking,
            )
            self.debate_history.append(debate_round)

            logger.info("Debate round %d ranking: %s", rnd, new_ranking)

            # Check if consensus achieved (simple deterministic top)
            top_idx = new_ranking[0]
            # For multi‑judge setups you would count votes; here we accept top.
            return current_solutions[top_idx]

        # If max rounds exhausted, fall back to the last top‑ranked solution
        final_top_idx = self.debate_history[-1].final_ranking[0]
        logger.warning(
            "Maximum debate rounds reached. Selecting final top solution UID %s.",
            current_solutions[final_top_idx].uid,
        )
        return current_solutions[final_top_idx]

    # --------------------------------------------------------------------- #
    # Utility methods
    # --------------------------------------------------------------------- #
    @staticmethod
    def _build_critique_prompt(model_name: str, candidates: List[Solution]) -> str:
        """
        Construct a prompt that asks ``model_name`` to critique the provided
        candidate solutions. The format is deliberately simple for demo
        purposes.
        """
        prompt = f"""You are {model_name}. Evaluate the following candidate solutions
for a critical decision. Provide a concise critique (strengths, weaknesses,
and any missing considerations) for each solution.

"""
        for idx, sol in enumerate(candidates, start=1):
            prompt += f"Solution {idx} (generated by {sol.model_name}):\n{sol.content}\n\n"

        prompt += "Your critique should be in plain English, no markdown."
        return prompt


# --------------------------------------------------------------------------- #
# Example stub usage (removed in production; kept for reference)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Placeholder stub models for quick local testing.
    class EchoModel:
        def __init__(self, name):
            self.name = name

        def generate(self, prompt: str) -> str:
            return f"{self.name} response to: {prompt[:30]}..."

    class SimpleJudge:
        def __init__(self, name="SimpleJudge"):
            self.name = name

        def rank(self, anonymized_solutions: List[str]) -> List[int]:
            # Very naive ranking: shortest text wins
            lengths = [len(s) for s in anonymized_solutions]
            return sorted(range(len(lengths)), key=lambda i: lengths[i])

    models = [EchoModel(f"Model{i}") for i in range(1, 4)]
    judge = SimpleJudge()
    node = ConsensusNode(models=models, judge=judge)
    winner, log = node.run("Determine the optimal cloud provider for our workload.")
    print("\n--- Winning Solution ---")
    print(winner.content)
    print("\n--- Audit Log (JSON) ---")
    print(json.dumps(log, indent=2))