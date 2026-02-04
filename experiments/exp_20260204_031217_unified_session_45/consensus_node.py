"""
consensus_node.py
-----------------

Implementation of the **multi‑model debate** protocol used for critical decision making
within the unified session experiment (exp_20260204_031217_unified_session_45).

The protocol follows the 3‑round flow described in **SWARM_ARCHITECTURE_V2.md**:

1. **GENERATION** – Three independent language models each generate a candidate
   solution to the supplied problem prompt.
2. **BLIND JUDGING** – The three candidates are anonymised and handed to a set of
   judges (which may be the same models or external evaluators).  Each judge ranks
   the solutions without knowledge of their origin.
3. **DEBATE** – If the blind‑judging round does not yield a clear consensus
   (i.e. no single solution receives a strict majority), the models enter a
   structured debate.  Each model may critique the others and propose refinements.
   All dissenting opinions are logged for auditability.

The public API consists of the :class:`ConsensusNode` class with a single
``run(prompt)`` method that returns the final agreed‑upon solution (or the best
available candidate when consensus cannot be reached).

Only new files may be written; core system files remain read‑only.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Protocol, Tuple, Dict, Any

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Protocols / Interfaces
# --------------------------------------------------------------------------- #
class ModelInterface(Protocol):
    """A minimal interface that any participating model must implement."""

    def generate_solution(self, prompt: str) -> str:
        """Return a free‑form solution string for the given prompt."""
        ...

    def rank_solutions(self, anonymized_solutions: List[str]) -> List[int]:
        """
        Given a list of anonymized solution strings, return a ranking as a list
        of indices (0‑based) ordered from most‑preferred to least‑preferred.
        """
        ...


# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class Candidate:
    """Container for a model‑generated candidate solution."""
    model_id: str
    solution: str
    anon_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# --------------------------------------------------------------------------- #
# Core consensus node implementation
# --------------------------------------------------------------------------- #
class ConsensusNode:
    """
    Orchestrates the 3‑round debate protocol across three models.

    Parameters
    ----------
    models : List[ModelInterface]
        Exactly three model instances that conform to :class:`ModelInterface`.
    judges : List[ModelInterface] | None
        Optional explicit judges.  If ``None`` the same three models are used as
        judges (the typical configuration described in the architecture doc).
    """

    def __init__(
        self,
        models: List[ModelInterface],
        judges: List[ModelInterface] | None = None,
    ) -> None:
        if len(models) != 3:
            raise ValueError("ConsensusNode requires exactly three generation models.")
        self.models = models
        self.judges = judges if judges is not None else models
        logger.debug("ConsensusNode initialised with %d models and %d judges.", len(models), len(self.judges))

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def run(self, prompt: str) -> str:
        """
        Execute the full debate protocol for *prompt* and return the final solution.

        Returns
        -------
        str
            The consensus solution (or the best‑ranked candidate if consensus is not
            achieved after the debate stage).
        """
        logger.info("=== Consensus protocol started ===")
        candidates = self._generation_round(prompt)
        logger.info("Generation round completed. Candidates: %s", [c.anon_id for c in candidates])

        ranking = self._blind_judging_round(candidates)
        logger.info("Blind judging completed. Ranking: %s", ranking)

        consensus_solution = self._evaluate_consensus(candidates, ranking)
        if consensus_solution:
            logger.info("Consensus reached after judging.")
            return consensus_solution

        logger.info("No consensus after judging – entering debate stage.")
        final_solution = self._debate_round(candidates, prompt)
        logger.info("Debate concluded. Final solution selected.")
        return final_solution

    # ------------------------------------------------------------------- #
    # Private helpers – each protocol round
    # ------------------------------------------------------------------- #
    def _generation_round(self, prompt: str) -> List[Candidate]:
        """Round 1 – each model generates a solution."""
        candidates = []
        for idx, model in enumerate(self.models):
            model_id = f"model_{idx + 1}"
            try:
                solution = model.generate_solution(prompt)
                logger.debug("Model %s generated solution.", model_id)
            except Exception as exc:  # pragma: no cover – safety net
                logger.error("Model %s failed to generate solution: %s", model_id, exc)
                solution = ""
            candidates.append(Candidate(model_id=model_id, solution=solution))
        return candidates

    def _blind_judging_round(self, candidates: List[Candidate]) -> List[int]:
        """
        Round 2 – anonymise candidates and collect rankings from each judge.

        Returns
        -------
        List[int]
            A flat list of candidate indices ordered by aggregated score
            (most‑preferred first).
        """
        anon_solutions = [c.solution for c in candidates]  # order is preserved
        aggregated_scores: Counter[int] = Counter()

        for judge_idx, judge in enumerate(self.judges):
            try:
                ranking = judge.rank_solutions(anon_solutions)
                logger.debug("Judge %d ranking: %s", judge_idx + 1, ranking)
                for position, cand_idx in enumerate(ranking):
                    # Higher rank (lower position) gets more points
                    aggregated_scores[cand_idx] += len(candidates) - position
            except Exception as exc:  # pragma: no cover
                logger.error("Judge %d failed ranking: %s", judge_idx + 1, exc)

        # Sort candidates by total score descending
        sorted_by_score = [idx for idx, _ in aggregated_scores.most_common()]
        # Ensure all candidates appear (in case of ties or missing scores)
        missing = set(range(len(candidates))) - set(sorted_by_score)
        sorted_by_score.extend(sorted(missing))
        return sorted_by_score

    def _evaluate_consensus(self, candidates: List[Candidate], ranking: List[int]) -> str | None:
        """
        Determine whether a strict majority exists for the top‑ranked candidate.

        Returns the solution string if consensus is achieved, otherwise ``None``.
        """
        top_idx = ranking[0]
        top_candidate = candidates[top_idx]

        # Count how many judges placed the top candidate first.
        first_place_votes = 0
        for judge in self.judges:
            try:
                rank = judge.rank_solutions([c.solution for c in candidates])
                if rank[0] == top_idx:
                    first_place_votes += 1
            except Exception:
                continue

        logger.debug("Top candidate %s received %d first‑place votes.", top_candidate.anon_id, first_place_votes)

        if first_place_votes > len(self.judges) // 2:
            logger.info("Consensus achieved: candidate %s", top_candidate.anon_id)
            return top_candidate.solution
        return None

    def _debate_round(self, candidates: List[Candidate], prompt: str) -> str:
        """
        Round 3 – structured debate.

        Each model may critique the others.  For simplicity we let each model
        re‑generate a solution after seeing the other candidates.  All dissenting
        opinions (i.e., any critique that disagrees with the eventual winner) are
        logged.

        The final selection follows the same blind‑judging aggregation on the
        updated solutions.
        """
        # Let each model see the other solutions and produce a refined answer.
        refined_candidates = []
        for idx, model in enumerate(self.models):
            other_solutions = "\n---\n".join(
                f"Solution {i+1}:\n{c.solution}" for i, c in enumerate(candidates) if i != idx
            )
            augmented_prompt = (
                f"{prompt}\n\n"
                f"The following alternative solutions have been proposed:\n{other_solutions}\n\n"
                "Based on this information, provide an improved solution."
            )
            try:
                refined = model.generate_solution(augmented_prompt)
                logger.debug("Model %s produced refined solution.", f"model_{idx+1}")
            except Exception as exc:  # pragma: no cover
                logger.error("Model %s failed to refine solution: %s", f"model_{idx+1}", exc)
                refined = candidates[idx].solution  # fallback to original

            refined_candidates.append(Candidate(model_id=f"model_{idx+1}", solution=refined))

        # Re‑run blind judging on refined solutions
        final_ranking = self._blind_judging_round(refined_candidates)
        winner_idx = final_ranking[0]
        winner = refined_candidates[winner_idx]

        # Log dissenting opinions: any model that did NOT produce the winning solution
        for idx, cand in enumerate(refined_candidates):
            if idx != winner_idx:
                logger.info(
                    "Dissenting opinion – Model %s did not align with consensus. "
                    "Solution excerpt: %s",
                    cand.model_id,
                    cand.solution[:200].replace("\n", " ") + ("..." if len(cand.solution) > 200 else ""),
                )
        return winner.solution

# --------------------------------------------------------------------------- #
# Example stub models (for illustration / testing)
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    class EchoModel:
        """A trivial model that echoes the prompt with an identifier."""
        def __init__(self, name: str):
            self.name = name

        def generate_solution(self, prompt: str) -> str:
            return f"{self.name} solution to: {prompt[:50]}..."

        def rank_solutions(self, anonymized_solutions: List[str]) -> List[int]:
            # Simple deterministic ranking: shortest solution first
            return sorted(range(len(anonymized_solutions)), key=lambda i: len(anonymized_solutions[i]))

    # Instantiate three stub models
    models = [EchoModel(f"Model{i}") for i in range(1, 4)]

    node = ConsensusNode(models=models)
    result = node.run("Explain the importance of version control in software engineering.")
    print("\nFinal consensus solution:\n", result)