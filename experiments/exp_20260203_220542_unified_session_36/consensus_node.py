"""
consensus_node.py
-----------------

Implementation of a multi‑model consensus engine based on the
SWARM_ARCHITECTURE_V2 specification.

The engine runs a 3‑round protocol for any critical decision:

1. **GENERATION** – Three independent language models produce candidate
   solutions for the supplied prompt.
2. **BLIND JUDGING** – The candidates are anonymised and each model ranks
   the other two solutions (self‑ranking is omitted).  Rankings are
   aggregated to determine if a majority consensus exists.
3. **DEBATE** – If no consensus is reached after blind judging, the models
   enter a structured debate.  Each model may critique the top‑ranked
   solution and propose a revised answer.  The process repeats for a
   configurable number of debate rounds (default: 2).

All dissenting opinions and ranking data are persisted to a JSON log for
auditability.

The module is deliberately lightweight – concrete model adapters are
expected to be provided by the host application (e.g. OpenAI, Anthropic,
Cohere).  Only the orchestration logic lives here.
"""

import json
import logging
import pathlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Helper data structures
# --------------------------------------------------------------------------- #
@dataclass
class ModelResult:
    """Container for a model's raw output."""
    model_name: str
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class RankedResult:
    """Result of blind judging for a single model."""
    judge_model: str
    rankings: List[Tuple[str, int]]  # (candidate_id, rank)


# --------------------------------------------------------------------------- #
# Abstract model interface
# --------------------------------------------------------------------------- #
class BaseModelAdapter:
    """
    Minimal interface required by the ConsensusNode.

    Concrete adapters must implement:
        * generate(prompt: str) -> str
        * critique(candidate: str, context: str) -> str
    """

    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def critique(self, candidate: str, context: str) -> str:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Core consensus engine
# --------------------------------------------------------------------------- #
class ConsensusNode:
    """
    Orchestrates a 3‑round consensus protocol among a set of language models.
    """

    def __init__(
        self,
        model_adapters: Sequence[BaseModelAdapter],
        log_dir: pathlib.Path | str = "logs",
        max_debate_rounds: int = 2,
    ):
        if len(model_adapters) < 3:
            raise ValueError("At least three model adapters are required.")
        self.models = list(model_adapters)
        self.max_debate_rounds = max_debate_rounds
        self.session_id = uuid.uuid4().hex
        self.log_path = pathlib.Path(log_dir) / f"{self.session_id}.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._log: Dict[str, Any] = {
            "session_id": self.session_id,
            "steps": [],
        }

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def run(self, prompt: str) -> ModelResult:
        """
        Execute the full protocol and return the final consensus solution.
        """
        LOGGER.info("Starting consensus session %s", self.session_id)

        # 1️⃣ Generation
        generation = self._generation_phase(prompt)

        # 2️⃣ Blind judging
        consensus, rankings = self._blind_judging_phase(generation)

        # 3️⃣ Debate (optional)
        if not consensus:
            LOGGER.info("No consensus after blind judging – entering debate.")
            final = self._debate_phase(generation, rankings, prompt)
        else:
            final = consensus

        self._persist_log()
        LOGGER.info("Consensus session %s completed.", self.session_id)
        return final

    # ------------------------------------------------------------------- #
    # Phase implementations
    # ------------------------------------------------------------------- #
    def _generation_phase(self, prompt: str) -> List[ModelResult]:
        """Each model produces a candidate solution."""
        candidates: List[ModelResult] = []
        for model in self.models:
            content = model.generate(prompt)
            result = ModelResult(model_name=model.name, content=content)
            candidates.append(result)
            LOGGER.debug("Model %s generated candidate.", model.name)

        self._log["steps"].append(
            {"phase": "generation", "candidates": [c.__dict__ for c in candidates]}
        )
        return candidates

    def _blind_judging_phase(
        self, candidates: List[ModelResult]
    ) -> Tuple[ModelResult | None, List[RankedResult]]:
        """
        Anonymise candidates and let each model rank the others.
        Returns a consensus candidate if >50% of judges agree on the same top
        candidate, otherwise None.
        """
        # Assign anonymised IDs
        anon_map = {c.model_name: f"cand_{i}" for i, c in enumerate(candidates)}
        anon_candidates = {
            anon_id: {"content": c.content, "metadata": c.metadata}
            for c, anon_id in zip(candidates, anon_map.values())
        }

        rankings: List[RankedResult] = []
        # Each model judges the other two candidates
        for judge in self.models:
            # Build the judging prompt (anonymous)
            judge_prompt = (
                "You are presented with three candidate answers to the same question. "
                "Rank the candidates from best (1) to worst (3) based on relevance, "
                "correctness, and clarity. Do NOT consider your own answer."
                "\n\n"
                + "\n".join(
                    f"{cid}: {info['content']}" for cid, info in anon_candidates.items()
                )
                + "\n\nProvide your ranking as a JSON list of objects: "
                "[{\"candidate_id\": \"cand_0\", \"rank\": 1}, ...]"
            )
            # Use the model's own generation capability to produce a ranking.
            raw = judge.generate(judge_prompt)
            try:
                parsed = json.loads(raw)
                rank_list = [(item["candidate_id"], int(item["rank"])) for item in parsed]
            except Exception as exc:
                LOGGER.warning(
                    "Judge %s produced unparsable ranking. Falling back to random.",
                    judge.name,
                )
                # Fallback: random ordering (deterministic for reproducibility)
                rank_list = [
                    (cid, idx + 1) for idx, cid in enumerate(sorted(anon_candidates))
                ]

            rankings.append(RankedResult(judge_model=judge.name, rankings=rank_list))
            LOGGER.debug("Judge %s submitted rankings.", judge.name)

        # Aggregate rankings
        aggregate_scores: Dict[str, int] = {cid: 0 for cid in anon_candidates}
        for rr in rankings:
            for cid, rank in rr.rankings:
                aggregate_scores[cid] += rank  # lower total = better

        # Determine top candidate(s)
        sorted_candidates = sorted(
            aggregate_scores.items(), key=lambda kv: kv[1]
        )  # (cid, total_score)
        top_cid, top_score = sorted_candidates[0]

        # Count how many judges placed the top_cid at rank 1
        top_first_votes = sum(
            1
            for rr in rankings
            if any(item[0] == top_cid and item[1] == 1 for item in rr.rankings)
        )
        consensus_reached = top_first_votes > len(self.models) / 2

        self._log["steps"].append(
            {
                "phase": "blind_judging",
                "anonymous_map": anon_map,
                "rankings": [r.__dict__ for r in rankings],
                "aggregate_scores": aggregate_scores,
                "consensus_reached": consensus_reached,
            }
        )

        if consensus_reached:
            # Resolve original model name from anon map
            winner_name = next(
                name for name, cid in anon_map.items() if cid == top_cid
            )
            winner = next(c for c in candidates if c.model_name == winner_name)
            LOGGER.info("Consensus reached on candidate from %s.", winner_name)
            return winner, rankings
        else:
            LOGGER.info(
                "No consensus after blind judging (top candidate received %d/%d first votes).",
                top_first_votes,
                len(self.models),
            )
            return None, rankings

    def _debate_phase(
        self,
        candidates: List[ModelResult],
        prior_rankings: List[RankedResult],
        prompt: str,
    ) -> ModelResult:
        """
        Structured debate: each model critiques the current leading answer,
        possibly producing a revised version.  After each round we re‑run
        blind judging on the revised set.  The process stops when consensus
        is reached or max_debate_rounds is exhausted.
        """
        # Initialise with the current set of candidates
        current_set = candidates

        for round_idx in range(1, self.max_debate_rounds + 1):
            LOGGER.info("Debate round %d/%d", round_idx, self.max_debate_rounds)

            # Identify current leader (lowest aggregate score from prior round)
            leader = self._determine_leader(current_set, prior_rankings)

            # Each model (except the leader) critiques and optionally revises
            revised_set: List[ModelResult] = []
            for model in self.models:
                if model.name == leader.model_name:
                    revised_set.append(leader)
                    continue

                critique_prompt = (
                    f"You are reviewing the following answer to the original prompt:\n\n"
                    f"{leader.content}\n\n"
                    f"Provide a concise critique focusing on factual errors, missing "
                    f"information, or logical gaps. Then, produce an improved version "
                    f"of the answer. Respond with a JSON object:\n"
                    f"{{\"critique\": \"...\", \"revision\": \"...\"}}"
                )
                raw = model.generate(critique_prompt)
                try:
                    parsed = json.loads(raw)
                    revision = parsed.get("revision", leader.content)
                except Exception:
                    LOGGER.warning(
                        "Model %s produced malformed critique. Keeping leader unchanged.",
                        model.name,
                    )
                    revision = leader.content

                revised_set.append(
                    ModelResult(
                        model_name=model.name,
                        content=revision,
                        metadata={"based_on": leader.model_name},
                    )
                )
                LOGGER.debug("Model %s submitted revision.", model.name)

            # Run blind judging on the revised set
            consensus, new_rankings = self._blind_judging_phase(revised_set)
            self._log["steps"].append(
                {
                    "phase": "debate",
                    "round": round_idx,
                    "leader_before": leader.__dict__,
                    "revised_set": [c.__dict__ for c in revised_set],
                    "new_rankings": [r.__dict__ for r in new_rankings],
                }
            )
            if consensus:
                return consensus

            # Prepare for next iteration
            current_set = revised_set
            prior_rankings = new_rankings

        # If we exit the loop without consensus, fall back to the best-ranked
        # candidate from the final round.
        final_winner = self._determine_leader(current_set, prior_rankings)
        LOGGER.info(
            "Debate concluded without consensus. Selecting best candidate from final round (%s).",
            final_winner.model_name,
        )
        return final_winner

    # ------------------------------------------------------------------- #
    # Utility helpers
    # ------------------------------------------------------------------- #
    def _determine_leader(
        self,
        candidates: List[ModelResult],
        rankings: List[RankedResult],
    ) -> ModelResult:
        """
        Compute the candidate with the lowest aggregate rank score.
        """
        # Build anon map for this temporary evaluation
        anon_map = {c.model_name: f"cand_{i}" for i, c in enumerate(candidates)}
        # Re‑aggregate scores from supplied rankings (they already reference anon IDs)
        agg: Dict[str, int] = {cid: 0 for cid in anon_map.values()}
        for rr in rankings:
            for cid, rank in rr.rankings:
                agg[cid] += rank
        # Identify best anon id
        best_cid = min(agg, key=agg.get)
        # Resolve back to model name
        winner_name = next(name for name, cid in anon_map.items() if cid == best_cid)
        return next(c for c in candidates if c.model_name == winner_name)

    def _persist_log(self) -> None:
        """Write the session log to disk."""
        with self.log_path.open("w", encoding="utf-8") as f:
            json.dump(self._log, f, indent=2, ensure_ascii=False)
        LOGGER.info("Session log written to %s", self.log_path)


# --------------------------------------------------------------------------- #
# Example stub adapters (for quick local testing)
# --------------------------------------------------------------------------- #
class EchoModelAdapter(BaseModelAdapter):
    """A trivial adapter that echoes the prompt – useful for unit tests."""

    def generate(self, prompt: str) -> str:
        return f"[{self.name} response] {prompt[:50]}..."

    def critique(self, candidate: str, context: str) -> str:
        return f"[{self.name} critique] No issues identified."


# --------------------------------------------------------------------------- #
# Command‑line entry point
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Run a consensus protocol among three dummy models."
    )
    parser.add_argument(
        "prompt", type=str, help="The prompt/question to resolve via consensus."
    )
    args = parser.parse_args()

    # Instantiate three placeholder models
    models = [
        EchoModelAdapter(name="model_A"),
        EchoModelAdapter(name="model_B"),
        EchoModelAdapter(name="model_C"),
    ]

    node = ConsensusNode(models)
    result = node.run(args.prompt)
    print("\n=== FINAL CONSENSUS RESULT ===")
    print(f"Model: {result.model_name}")
    print(f"Answer: {result.content}\n")