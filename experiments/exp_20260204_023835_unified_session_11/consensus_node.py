"""
consensus_node.py
-----------------

Implements the multi‑model “consensus node” used by the unified session experiment.
The node follows the 3‑round protocol described in **SWARM_ARCHITECTURE_V2.md**:

1. **Generation** – Three independent LLM “agents” generate candidate solutions.
2. **Blind Judging** – The candidates are anonymised and each agent ranks the
   others’ outputs.  A consensus is reached if a majority (>50 %) agrees on the
   top‑ranked solution.
3. **Debate** – If no consensus is reached, agents enter a short debate where
   they iteratively critique the most‑voted candidate.  After a fixed number of
   debate turns the rankings are recomputed; if still no consensus the
   highest‑ranked candidate is returned together with a log of dissenting
   opinions.

Only the orchestration logic lives here – concrete model wrappers are expected
to expose a ``generate(prompt) -> str`` method and a ``critique(candidate) -> str``
method.  The node loads them dynamically via a simple registry (see
``model_registry`` below).  This design keeps the file self‑contained and
compatible with the experiment sandbox.

"""

import logging
import random
from typing import List, Dict, Tuple, Callable

# --------------------------------------------------------------------------- #
# Logging configuration – all nodes write to the experiment’s logger.
# --------------------------------------------------------------------------- #
logger = logging.getLogger("consensus_node")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s – %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Simple model registry.
# --------------------------------------------------------------------------- #
# In a real deployment each entry would be a class that wraps a specific LLM.
# For the purpose of the experiment we provide a very lightweight mock that
# can be swapped out with real implementations.
# --------------------------------------------------------------------------- #
class MockModel:
    """A deterministic mock model used when no real LLM is supplied."""

    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str) -> str:
        # Produce a pseudo‑random but reproducible answer.
        random.seed(f"{self.name}:{prompt}")
        return f"{self.name} answer to '{prompt[:30]}...'"

    def critique(self, candidate: str) -> str:
        # Simple critique that mentions a random short flaw.
        flaws = [
            "lacks supporting evidence",
            "over‑generalises the premise",
            "contains ambiguous terminology",
            "ignores edge cases",
            "is overly verbose",
        ]
        random.seed(f"{self.name}:{candidate}")
        flaw = random.choice(flaws)
        return f"{self.name} critique: {flaw}."


# Registry mapping a short identifier to a callable that returns a model instance.
model_registry: Dict[str, Callable[[], MockModel]] = {
    "model_a": lambda: MockModel("ModelA"),
    "model_b": lambda: MockModel("ModelB"),
    "model_c": lambda: MockModel("ModelC"),
    # Real models can be registered here, e.g.:
    # "gpt4": lambda: RealGPT4Wrapper(),
}


# --------------------------------------------------------------------------- #
# Core consensus logic.
# --------------------------------------------------------------------------- #
class ConsensusNode:
    """
    Orchestrates a three‑round consensus protocol among three agents.

    Parameters
    ----------
    model_ids : List[str]
        Identifiers of the three models to use. Must be present in
        ``model_registry``.
    max_debate_turns : int, optional
        Number of critique rounds before giving up on consensus.
    """

    def __init__(self, model_ids: List[str], max_debate_turns: int = 2):
        if len(model_ids) != 3:
            raise ValueError("Exactly three model identifiers are required.")
        self.models = [model_registry[mid]() for mid in model_ids]
        self.max_debate_turns = max_debate_turns

    # ------------------------------------------------------------------- #
    # Public entry point.
    # ------------------------------------------------------------------- #
    def run(self, prompt: str) -> Tuple[str, List[str]]:
        """
        Executes the full protocol.

        Returns
        -------
        final_solution : str
            The selected solution after consensus (or after debate fallback).
        dissent_log : List[str]
            Human‑readable log of dissenting opinions collected during the
            debate phase.
        """
        logger.info("=== Consensus protocol started ===")
        logger.info(f"Prompt: {prompt}")

        # 1️⃣ Generation
        candidates = self._generation_phase(prompt)

        # 2️⃣ Blind judging
        consensus, rankings = self._blind_judging_phase(candidates)
        if consensus:
            logger.info("Consensus reached during blind judging.")
            return consensus, []

        # 3️⃣ Debate (fallback)
        final_solution, dissent_log = self._debate_phase(candidates, rankings)
        logger.info("=== Consensus protocol finished ===")
        return final_solution, dissent_log

    # ------------------------------------------------------------------- #
    # Phase implementations.
    # ------------------------------------------------------------------- #
    def _generation_phase(self, prompt: str) -> List[Tuple[str, str]]:
        """
        Each model generates a candidate solution.

        Returns
        -------
        List of (model_name, solution) tuples.
        """
        logger.info("🔧 Generation phase – each model creates a solution.")
        candidates = []
        for model in self.models:
            answer = model.generate(prompt)
            logger.debug(f"{model.name} generated: {answer}")
            candidates.append((model.name, answer))
        return candidates

    def _blind_judging_phase(
        self, candidates: List[Tuple[str, str]]
    ) -> Tuple[str | None, Dict[str, List[int]]]:
        """
        Models rank anonymised solutions.  Rankings are expressed as a list of
        candidate indices ordered from most to least preferred.

        Returns
        -------
        consensus_solution : str | None
            The solution if a strict majority agrees on the same top candidate.
        rankings : dict
            Mapping from model name to its ranking list.
        """
        logger.info("🕶️ Blind judging phase – anonymised ranking.")
        # Anonymise candidates: assign temporary IDs 0,1,2.
        anon_map = {idx: sol for idx, (_, sol) in enumerate(candidates)}
        # Shuffle order to avoid any positional bias.
        shuffled_ids = list(anon_map.keys())
        random.shuffle(shuffled_ids)

        # Collect rankings.
        rankings: Dict[str, List[int]] = {}
        top_votes: Dict[int, int] = {idx: 0 for idx in anon_map}
        for model in self.models:
            # Model sees only the texts, not the original author.
            visible_solutions = [anon_map[i] for i in shuffled_ids]
            # Simple ranking: the model scores each solution via a mock heuristic.
            # In a real system we would ask the model to output a ranking.
            scores = self._mock_score_solutions(model, visible_solutions)
            # Convert scores to ranking (lowest index = best).
            ranked_ids = [shuffled_ids[i] for i in sorted(range(len(scores)), key=lambda i: scores[i])]
            rankings[model.name] = ranked_ids
            top_votes[ranked_ids[0]] += 1
            logger.debug(f"{model.name} ranking: {ranked_ids}")

        # Determine if any candidate received >1 vote (majority of 3).
        for cand_id, votes in top_votes.items():
            if votes > 1:
                solution = anon_map[cand_id]
                logger.info(f"Candidate {cand_id} received {votes}/3 top votes – consensus.")
                return solution, rankings

        logger.info("No consensus after blind judging.")
        return None, rankings

    def _debate_phase(
        self,
        candidates: List[Tuple[str, str]],
        prior_rankings: Dict[str, List[int]],
    ) -> Tuple[str, List[str]]:
        """
        Conduct a short debate where each model critiques the current front‑runner.
        After each turn rankings are recomputed.  If consensus emerges early the
        loop stops; otherwise the best‑ranked candidate after the final turn is
        returned.

        Returns
        -------
        final_solution : str
        dissent_log : List[str] – collected critiques of non‑winning candidates.
        """
        logger.info("💬 Debate phase – iterative critique.")
        # Prepare structures.
        solution_by_id = {idx: sol for idx, (_, sol) in enumerate(candidates)}
        dissent_log: List[str] = []

        # Initial front‑runner based on prior rankings (most common top‑rank).
        front_runner_id = self._most_common_top(prior_rankings)
        logger.info(f"Initial front‑runner candidate ID: {front_runner_id}")

        for turn in range(self.max_debate_turns):
            logger.info(f"--- Debate turn {turn + 1}/{self.max_debate_turns} ---")
            front_solution = solution_by_id[front_runner_id]

            # Each model (including the one that originally proposed the front‑runner)
            # provides a critique.
            critiques = []
            for model in self.models:
                critique = model.critique(front_solution)
                critiques.append((model.name, critique))
                logger.debug(f"{model.name} critique: {critique}")

            # Store critiques that disagree with the front‑runner (simple heuristic:
            # any critique that mentions a flaw is considered dissent).
            dissent_log.extend([c for _, c in critiques])

            # Re‑rank based on the critiques – we simulate this by assigning a
            # random slight penalty to the front‑runner if any critique mentions
            # a specific keyword.
            penalty = any("flaw" in c.lower() for c in [c for _, c in critiques])
            if penalty:
                # Demote front‑runner by swapping with a random other candidate.
                other_ids = [i for i in solution_by_id if i != front_runner_id]
                if other_ids:
                    new_front = random.choice(other_ids)
                    logger.info(
                        f"Critiques introduced penalty – switching front‑runner from {front_runner_id} to {new_front}"
                    )
                    front_runner_id = new_front
            else:
                logger.info("No penalty detected – front‑runner remains unchanged.")
                # If no penalty, we assume consensus is reached.
                break

        final_solution = solution_by_id[front_runner_id]
        logger.info(f"Debate concluded. Selected candidate ID: {front_runner_id}")
        return final_solution, dissent_log

    # ------------------------------------------------------------------- #
    # Helper utilities.
    # ------------------------------------------------------------------- #
    @staticmethod
    def _mock_score_solutions(model: MockModel, solutions: List[str]) -> List[float]:
        """
        Produce deterministic pseudo‑scores for a list of solutions.
        Lower score = better.
        """
        scores = []
        for sol in solutions:
            random.seed(f"{model.name}:{sol}")
            scores.append(random.random())
        return scores

    @staticmethod
    def _most_common_top(rankings: Dict[str, List[int]]) -> int:
        """
        Given a dict of model -> ranking list, return the candidate ID that
        appears most frequently in the first position.
        """
        top_counts: Dict[int, int] = {}
        for rank in rankings.values():
            top = rank[0]
            top_counts[top] = top_counts.get(top, 0) + 1
        # Return the candidate with the highest count (ties broken arbitrarily).
        return max(top_counts, key=top_counts.get)


# --------------------------------------------------------------------------- #
# Simple CLI entry point for manual testing.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a consensus node.")
    parser.add_argument(
        "prompt", type=str, help="The prompt/question to be answered."
    )
    args = parser.parse_args()

    node = ConsensusNode(model_ids=["model_a", "model_b", "model_c"])
    solution, dissent = node.run(args.prompt)

    print("\n=== FINAL SOLUTION ===")
    print(solution)
    if dissent:
        print("\n=== DISSENT LOG ===")
        for line in dissent:
            print("- ", line)