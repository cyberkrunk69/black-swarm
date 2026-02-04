"""
consensus_node.py
-----------------

Implements a multi‑model debate / consensus engine based on the
SWARM_ARCHITECTURE_V2 specification.

The protocol runs in three distinct rounds:

1. **Generation** – Three independent language models are asked to produce
   candidate solutions to a given problem prompt.
2. **Blind Judging** – The generated solutions are anonymised and handed to a
   judging model (or a set of judges).  Each judge ranks the solutions without
   knowledge of their source.  If a super‑majority (≥2/3) agrees on the
   top‑ranked solution, consensus is reached.
3. **Debate** – If no consensus emerges, the top‑N solutions enter a debate
   round where each model is allowed to critique the others.  After the
   debate a second blind‑judging phase decides the winner.  All dissenting
   opinions are logged for auditability.

The engine is deliberately lightweight – it only orchestrates calls to
external model wrappers (``call_model``) which must be provided by the
hosting application.  The module is safe for inclusion in any experiment
folder; core system files remain untouched.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Logging configuration – each experiment gets its own logger.
# --------------------------------------------------------------------------- #
LOGGER_NAME = "consensus_node"
logger = logging.getLogger(LOGGER_NAME)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class GenerationResult:
    """Container for a single model's output."""

    model_id: str
    solution: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgingResult:
    """Result of a blind‑judging round."""

    rankings: List[Tuple[str, int]]  # List of (solution_id, rank) sorted by rank
    consensus_reached: bool
    winning_solution_id: str | None = None
    dissent_log: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Helper types
# --------------------------------------------------------------------------- #
ModelCallable = Callable[[str], asyncio.Future]  # async function that returns a str


# --------------------------------------------------------------------------- #
# Core consensus engine
# --------------------------------------------------------------------------- #
class ConsensusNode:
    """
    Orchestrates a three‑round consensus protocol among multiple LLMs.

    Parameters
    ----------
    generation_models:
        Mapping of model identifiers to async callables that accept a prompt
        and return a generated string.
    judging_models:
        Mapping of judge identifiers to async callables that accept a list of
        anonymised solutions and return a ranking list (list of solution ids in
        descending order of preference).
    debate_turns:
        Number of back‑and‑forth critique exchanges during the debate phase.
    """

    def __init__(
        self,
        generation_models: Dict[str, ModelCallable],
        judging_models: Dict[str, ModelCallable],
        debate_turns: int = 2,
    ) -> None:
        if len(generation_models) < 3:
            raise ValueError("At least three generation models are required.")
        self.generation_models = generation_models
        self.judging_models = judging_models
        self.debate_turns = debate_turns

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    async def run(self, problem_prompt: str) -> str:
        """
        Execute the full consensus protocol for ``problem_prompt`` and return the
        final chosen solution.

        Raises
        ------
        RuntimeError
            If consensus cannot be reached after the debate phase.
        """
        logger.info("Starting consensus protocol for prompt: %s", problem_prompt)

        # 1️⃣ Generation
        gen_results = await self._generation_round(problem_prompt)

        # 2️⃣ Blind judging
        judging_res = await self._blind_judging_round(gen_results)

        if judging_res.consensus_reached:
            logger.info(
                "Consensus reached after first judging round. Winning solution ID: %s",
                judging_res.winning_solution_id,
            )
            return self._lookup_solution(gen_results, judging_res.winning_solution_id)

        # 3️⃣ Debate (only if no consensus)
        logger.info("No consensus – entering debate phase.")
        debated_results = await self._debate_round(gen_results)

        # Second blind judging after debate
        final_judging_res = await self._blind_judging_round(debated_results)

        if final_judging_res.consensus_reached:
            logger.info(
                "Consensus reached after debate. Winning solution ID: %s",
                final_judging_res.winning_solution_id,
            )
            return self._lookup_solution(
                debated_results, final_judging_res.winning_solution_id
            )

        # If still no consensus, raise an error – the caller can decide fallback.
        logger.error("Consensus could not be reached after debate.")
        raise RuntimeError("Unable to reach consensus after debate phase.")

    # ------------------------------------------------------------------- #
    # Internal steps
    # ------------------------------------------------------------------- #
    async def _generation_round(self, prompt: str) -> List[GenerationResult]:
        """Ask each generation model for a solution."""
        logger.info("Generation round – %d models", len(self.generation_models))
        tasks = []
        for model_id, model_fn in self.generation_models.items():
            task = asyncio.create_task(self._call_model(model_id, model_fn, prompt))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=False)
        logger.debug("Generation results: %s", results)
        return results

    async def _call_model(
        self, model_id: str, model_fn: ModelCallable, prompt: str
    ) -> GenerationResult:
        """Wrap a model call with logging and metadata."""
        logger.debug("Calling generation model %s", model_id)
        solution = await model_fn(prompt)
        return GenerationResult(
            model_id=model_id,
            solution=solution,
            metadata={"model_id": model_id, "timestamp": uuid.uuid4().hex},
        )

    async def _blind_judging_round(
        self, gen_results: List[GenerationResult]
    ) -> JudgingResult:
        """
        Perform blind judging on the supplied solutions.

        The solutions are anonymised (assigned a UUID) before being sent to each
        judging model.  Rankings from all judges are aggregated.  Consensus is
        defined as a super‑majority (≥2/3 of judges) agreeing on the same top
        solution.
        """
        logger.info("Blind judging round – %d judges", len(self.judging_models))

        # Anonymise solutions
        anon_map = {str(uuid.uuid4()): res for res in gen_results}
        anon_solutions = [
            {"id": anon_id, "text": res.solution} for anon_id, res in anon_map.items()
        ]

        # Gather rankings from each judge
        judge_tasks = []
        for judge_id, judge_fn in self.judging_models.items():
            task = asyncio.create_task(
                self._call_judge(judge_id, judge_fn, anon_solutions)
            )
            judge_tasks.append(task)

        judge_rankings = await asyncio.gather(*judge_tasks, return_exceptions=False)

        # Aggregate rankings
        top_counts = Counter()
        dissent_log = []

        for judge_id, ranking in judge_rankings:
            if not ranking:
                continue
            top_solution_id = ranking[0]
            top_counts[top_solution_id] += 1
            logger.debug("Judge %s ranked %s first", judge_id, top_solution_id)

        # Determine if any solution has super‑majority
        total_judges = len(judge_rankings)
        consensus_solution_id = None
        consensus = False
        for sol_id, cnt in top_counts.items():
            if cnt >= (2 * total_judges) // 3 + 1:  # ≥ 2/3 majority
                consensus = True
                consensus_solution_id = sol_id
                break

        # Build ordered ranking list (most votes first)
        ordered = [
            (sol_id, cnt) for sol_id, cnt in top_counts.most_common()
        ]

        # Log dissenting opinions (any judge that didn't pick the consensus)
        if consensus:
            for judge_id, ranking in judge_rankings:
                if ranking[0] != consensus_solution_id:
                    dissent_log.append(
                        f"Judge {judge_id} dissent: preferred {ranking[0]}, "
                        f"consensus {consensus_solution_id}"
                    )
        else:
            dissent_log.append("No consensus reached in this judging round.")

        return JudgingResult(
            rankings=ordered,
            consensus_reached=consensus,
            winning_solution_id=consensus_solution_id,
            dissent_log=dissent_log,
        )

    async def _call_judge(
        self,
        judge_id: str,
        judge_fn: ModelCallable,
        anon_solutions: List[Dict[str, str]],
    ) -> Tuple[str, List[str]]:
        """
        Ask a judging model to rank the anonymised solutions.

        Expected format for ``judge_fn``: receives a prompt string that includes
        the list of solutions and returns a newline‑separated list of solution
        IDs ordered by preference.
        """
        # Build a simple prompt for the judge
        prompt_lines = ["Rank the following solutions from best to worst.\n"]
        for sol in anon_solutions:
            prompt_lines.append(f"ID: {sol['id']}\nSolution: {sol['text']}\n")
        prompt_lines.append("\nProvide only the IDs in order, one per line.")
        prompt = "\n".join(prompt_lines)

        logger.debug("Calling judge %s", judge_id)
        raw_output = await judge_fn(prompt)

        # Parse the judge's output – keep only valid IDs
        ranking = [
            line.strip()
            for line in raw_output.splitlines()
            if line.strip() in {s["id"] for s in anon_solutions}
        ]
        return judge_id, ranking

    async def _debate_round(
        self, gen_results: List[GenerationResult]
    ) -> List[GenerationResult]:
        """
        Conduct a structured debate among the top‑N solutions.

        The debate is a simple turn‑based exchange where each model receives a
        prompt containing:
          * Its own solution
          * The opponent solutions
          * The previous critique (if any)

        Each model returns a critique string.  After ``debate_turns`` cycles we
        concatenate all critiques to the original solutions, producing a new
        set of enriched solutions that are fed into a second judging round.
        """
        logger.info(
            "Debate round – %d turns, %d participating solutions",
            self.debate_turns,
            len(gen_results),
        )

        # Prepare mutable copies of solutions
        enriched = {res.model_id: res.solution for res in gen_results}

        for turn in range(self.debate_turns):
            logger.debug("Debate turn %d", turn + 1)
            critique_tasks = []
            for model_id, model_fn in self.generation_models.items():
                # Build critique prompt
                opponent_texts = [
                    f"[{mid}] {txt}"
                    for mid, txt in enriched.items()
                    if mid != model_id
                ]
                critique_prompt = (
                    "You are participating in a debate. Your original solution is:\n"
                    f"{enriched[model_id]}\n\n"
                    "The opponent solutions are:\n"
                    + "\n".join(opponent_texts)
                    + "\n\nProvide a concise critique of the opponent solutions "
                    "and suggest improvements to your own approach."
                )
                task = asyncio.create_task(
                    self._call_model(model_id, model_fn, critique_prompt)
                )
                critique_tasks.append((model_id, task))

            # Gather critiques
            for model_id, task in critique_tasks:
                critique = await task
                # Append critique to the solution for the next round
                enriched[model_id] = f"{enriched[model_id]}\n\n--- Critique Turn {turn+1} ---\n{critique}"

        # Convert back to GenerationResult list (preserve original metadata)
        debated_results = []
        for res in gen_results:
            debated_results.append(
                GenerationResult(
                    model_id=res.model_id,
                    solution=enriched[res.model_id],
                    metadata=res.metadata,
                )
            )
        return debated_results

    # ------------------------------------------------------------------- #
    # Utility helpers
    # ------------------------------------------------------------------- #
    @staticmethod
    def _lookup_solution(
        results: List[GenerationResult], solution_id: str
    ) -> str:
        """Return the solution text that matches the anonymised ``solution_id``."""
        for res in results:
            # The anonymised ID is stored in metadata during generation; if not
            # present we fall back to direct match on model_id.
            if res.metadata.get("anon_id") == solution_id or res.model_id == solution_id:
                return res.solution
        # If we cannot find a direct match, attempt a reverse lookup via the
        # original anonymisation map (used only inside the node).
        raise ValueError(f"Solution ID {solution_id} not found among generation results.")

# --------------------------------------------------------------------------- #
# Example usage (for reference – not executed on import)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import os

    async def dummy_model(prompt: str) -> str:
        """A placeholder async model that echoes the prompt."""
        await asyncio.sleep(0.1)
        return f"Response to: {prompt[:50]}..."

    # Build minimal model dictionaries
    gen_models = {
        "model_A": dummy_model,
        "model_B": dummy_model,
        "model_C": dummy_model,
    }
    judge_models = {"judge_1": dummy_model, "judge_2": dummy_model, "judge_3": dummy_model}

    node = ConsensusNode(gen_models, judge_models, debate_turns=1)

    async def run_demo():
        result = await node.run("Explain the importance of data provenance.")
        print("\nFinal consensus solution:\n", result)

    asyncio.run(run_demo())