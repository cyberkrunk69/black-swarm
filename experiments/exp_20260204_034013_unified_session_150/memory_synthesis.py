import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

_LESSONS_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # experiments/exp_20260204_034013_unified_session_150
        "..", "..", "learned_lessons.json",
    )
)

def _now_ts() -> float:
    """Current timestamp as float seconds since epoch."""
    return time.time()


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Core synthesis logic
# --------------------------------------------------------------------------- #

def load_all_lessons() -> List[Dict[str, Any]]:
    """
    Load the learned_lessons.json file and return a flat list of lesson dicts.
    Expected schema for each lesson (example):
    {
        "id": "<uuid>",
        "text": "Never trust a stranger with your password.",
        "category": "security",
        "retrieval_count": 5,
        "last_retrieved": 1700000000.0,   # epoch seconds
        "impact": 0.8                     # 0..1 importance as judged by the system
    }
    """
    if not os.path.exists(_LESSONS_PATH):
        return []

    data = _load_json(_LESSONS_PATH)

    # The JSON may be a dict with categories or a plain list.
    if isinstance(data, dict):
        # Flatten all values assuming they are lists of lessons.
        lessons = []
        for v in data.values():
            if isinstance(v, list):
                lessons.extend(v)
        return lessons
    elif isinstance(data, list):
        return data
    else:
        # Unexpected format – return empty list to avoid crashes.
        return []


def compute_importance(lesson: Dict[str, Any]) -> float:
    """
    Compute a scalar importance score for a lesson.
    Factors:
      * retrieval frequency (log-scaled)
      * recency (exponential decay)
      * impact (provided by the system)
    Returns a float where higher means more important.
    """
    retrieval = lesson.get("retrieval_count", 0)
    impact = lesson.get("impact", 0.0)

    # Recency: newer lessons are more relevant.
    last_ts = lesson.get("last_retrieved", 0.0)
    age_seconds = max(_now_ts() - last_ts, 0.0)
    # Half‑life of 7 days.
    recency_factor = 0.5 ** (age_seconds / (7 * 24 * 3600))

    # Retrieval factor: log(1 + n) to dampen huge counts.
    retrieval_factor = (1 + retrieval) ** 0.5

    # Combine (weights can be tuned later).
    importance = (0.4 * retrieval_factor) + (0.4 * recency_factor) + (0.2 * impact)
    return importance


def _batch_lessons_by_category(lessons: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group lessons by their 'category' field for later pattern detection."""
    buckets = defaultdict(list)
    for l in lessons:
        cat = l.get("category", "uncategorized")
        buckets[cat].append(l)
    return buckets


def generate_reflection(lessons_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Produce a higher‑level reflection from a batch of lessons.
    The reflection contains:
      * id – generated UUID‑like string
      * text – synthesized insight
      * source_ids – list of lesson ids that contributed
      * level – integer hierarchy level (1 = pattern, 2 = principle)
      * created – timestamp
    """
    import uuid

    # Simple heuristic: concatenate unique key phrases.
    # In a real system you would use an LLM; here we approximate.
    unique_texts = list({l["text"] for l in lessons_batch})
    synthesized = " ; ".join(sorted(unique_texts))

    reflection = {
        "id": str(uuid.uuid4()),
        "text": synthesized,
        "source_ids": [l["id"] for l in lessons_batch if "id" in l],
        "level": 1,  # default; caller may promote to 2 later
        "created": _now_ts(),
    }
    return reflection


def prune_redundant(lessons: List[Dict[str, Any]], reflections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove lessons that are fully subsumed by any reflection.
    A lesson is considered subsumed if its id appears in reflection['source_ids'].
    Returns a new list of lessons that remain.
    """
    covered_ids = {sid for refl in reflections for sid in refl.get("source_ids", [])}
    pruned = [l for l in lessons if l.get("id") not in covered_ids]
    return pruned


# --------------------------------------------------------------------------- #
# Hierarchy management
# --------------------------------------------------------------------------- #

class ReflectionSynthesizer:
    """
    Orchestrates periodic synthesis, promotion, and archiving.
    """

    def __init__(self, lessons_path: str = _LESSONS_PATH):
        self.lessons_path = lessons_path
        self._load_state()

    def _load_state(self) -> None:
        """Load lessons and any existing reflections."""
        raw = _load_json(self.lessons_path) if os.path.exists(self.lessons_path) else []
        # Normalise to flat list.
        if isinstance(raw, dict):
            self.lessons = []
            for v in raw.values():
                if isinstance(v, list):
                    self.lessons.extend(v)
        else:
            self.lessons = list(raw)

        # Reflections are stored together with lessons under a special key.
        self.reflections: List[Dict[str, Any]] = []
        if isinstance(raw, dict) and "reflections" in raw:
            self.reflections = raw["reflections"]

    def _persist(self) -> None:
        """Write lessons and reflections back to JSON."""
        # Preserve possible category grouping if original file was dict‑based.
        if isinstance(_load_json(self.lessons_path), dict):
            # Re‑group lessons by original categories (fallback to 'uncategorized').
            categories = defaultdict(list)
            for l in self.lessons:
                cat = l.get("category", "uncategorized")
                categories[cat].append(l)
            payload = dict(categories)
            payload["reflections"] = self.reflections
        else:
            payload = self.lessons + self.reflections
        _dump_json(self.lessons_path, payload)

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def run_synthesis_cycle(self) -> None:
        """
        Execute a full synthesis step:
          1. Compute importance for all lessons.
          2. Identify level‑0 patterns (appear ≥3 times).
          3. Generate level‑1 reflections (patterns).
          4. Identify cross‑category patterns → level‑2 principles.
          5. Prune redundant lessons.
          6. Archive lessons with very low importance.
        """
        # 1. Score lessons
        for l in self.lessons:
            l["importance"] = compute_importance(l)

        # 2. Detect frequent lessons (pattern candidates)
        text_counter = Counter(l["text"] for l in self.lessons)
        frequent_texts = {txt for txt, cnt in text_counter.items() if cnt >= 3}

        # Gather lessons that belong to each frequent text.
        pattern_groups: List[List[Dict[str, Any]]] = []
        for txt in frequent_texts:
            group = [l for l in self.lessons if l["text"] == txt]
            pattern_groups.append(group)

        # 3. Generate level‑1 reflections from each pattern group.
        new_reflections: List[Dict[str, Any]] = []
        for group in pattern_groups:
            refl = generate_reflection(group)
            refl["level"] = 1
            new_reflections.append(refl)

        # 4. Cross‑category principle synthesis (level‑2)
        # Group reflections by category of their source lessons.
        cat_to_reflections: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for refl in new_reflections:
            # Determine dominant category among its sources.
            src_cats = [
                l.get("category", "uncategorized")
                for l in self.lessons
                if l.get("id") in refl.get("source_ids", [])
            ]
            if src_cats:
                dominant = Counter(src_cats).most_common(1)[0][0]
            else:
                dominant = "uncategorized"
            cat_to_reflections[dominant].append(refl)

        # If a principle spans ≥2 categories, promote to level‑2.
        for cat, refls in cat_to_reflections.items():
            if len(refls) >= 2:
                principle = {
                    "id": f"principle-{cat}-{int(_now_ts())}",
                    "text": " | ".join(r["text"] for r in refls),
                    "source_ids": [sid for r in refls for sid in r.get("source_ids", [])],
                    "level": 2,
                    "created": _now_ts(),
                }
                new_reflections.append(principle)

        # 5. Prune redundant lessons
        self.lessons = prune_redundant(self.lessons, new_reflections)

        # 6. Archive rarely‑used lessons (importance < 0.15)
        archive_cutoff = 0.15
        self.lessons = [l for l in self.lessons if l.get("importance", 0) >= archive_cutoff]

        # Append new reflections to existing list
        self.reflections.extend(new_reflections)

        # Persist changes
        self._persist()

    # ------------------------------------------------------------------- #
    # Utility for external callers (e.g., after grind sessions)
    # ------------------------------------------------------------------- #

    def maybe_trigger(self, grind_counter: int) -> None:
        """
        Called after a grind session. If `grind_counter` is a multiple of 10,
        run the synthesis cycle.
        """
        if grind_counter % 10 == 0:
            self.run_synthesis_cycle()


# --------------------------------------------------------------------------- #
# Convenience entry‑point (can be used from the CLI)
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run memory synthesis for learned lessons.")
    parser.add_argument(
        "--counter",
        type=int,
        default=0,
        help="Current grind session counter; synthesis runs when divisible by 10.",
    )
    args = parser.parse_args()

    synth = ReflectionSynthesizer()
    synth.maybe_trigger(args.counter)
    print(f"Synthesis completed. Lessons: {len(synth.lessons)}. Reflections: {len(synth.reflections)}.")