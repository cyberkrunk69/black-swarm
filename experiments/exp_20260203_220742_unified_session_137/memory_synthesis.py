"""
memory_synthesis.py

Implements reflection synthesis for the generative‑agents memory system.
The module works on the `learned_lessons.json` store located at the project root.
It provides:
* loading of all lessons,
* importance scoring,
* batch reflection generation,
* redundancy pruning,
* a simple hierarchy (raw → patterns → principles),
* a helper `run_periodic_synthesis` that can be called after every 10 grind sessions.
"""

import json
import os
import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LESSONS_PATH = os.path.join(PROJECT_ROOT, "learned_lessons.json")

# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #
def _now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _dump_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Core API
# --------------------------------------------------------------------------- #
def load_all_lessons() -> List[Dict[str, Any]]:
    """
    Load the flat list of all lessons from ``learned_lessons.json``.
    The file is expected to contain a JSON list where each entry is a dict
    with at least the keys:
        - ``text``: the lesson content
        - ``category``: optional grouping label
        - ``retrieval_count``: how many times the lesson has been used
        - ``last_retrieved``: ISO timestamp of the most recent retrieval
        - ``impact``: numeric score (0‑1) representing perceived impact
        - ``level``: 0 (raw), 1 (pattern), 2 (principle)
    Missing fields are auto‑filled with defaults.
    """
    if not os.path.exists(LESSONS_PATH):
        # Initialise an empty store if missing
        _dump_json([], LESSONS_PATH)
        return []

    lessons = _load_json(LESSONS_PATH)
    # Normalise fields
    for l in lessons:
        l.setdefault("retrieval_count", 0)
        l.setdefault("last_retrieved", "1970-01-01T00:00:00Z")
        l.setdefault("impact", 0.0)
        l.setdefault("category", "uncategorized")
        l.setdefault("level", 0)
    return lessons


def compute_importance(lesson: Dict[str, Any]) -> float:
    """
    Compute a scalar importance score for a lesson.

    Importance = w1 * frequency + w2 * recency + w3 * impact

    * frequency  – normalized retrieval count (log‑scaled)
    * recency    – exponential decay based on days since last retrieval
    * impact     – the stored impact field (0‑1)

    Returns a float in the range [0, 1].
    """
    # Frequency (log‑scaled)
    freq = lesson.get("retrieval_count", 0)
    freq_score = min(1.0, (1 + (freq if freq > 0 else 0)) ** 0.5 / 10)

    # Recency
    try:
        last = datetime.datetime.fromisoformat(
            lesson.get("last_retrieved", "1970-01-01T00:00:00Z".replace("Z", ""))
        )
    except ValueError:
        last = datetime.datetime(1970, 1, 1)
    days_since = (datetime.datetime.utcnow() - last).days
    # Half‑life of 30 days
    recency_score = 1.0 / (1.0 + (days_since / 30.0))

    # Impact (already 0‑1)
    impact_score = float(lesson.get("impact", 0.0))
    # Weighted sum (weights sum to 1)
    w1, w2, w3 = 0.4, 0.3, 0.3
    importance = w1 * freq_score + w2 * recency_score + w3 * impact_score
    return round(min(max(importance, 0.0), 1.0), 4)


def generate_reflection(lessons_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize a higher‑level insight from a batch of lessons.
    The function extracts common keywords, builds a concise summary,
    and assigns it level 1 (pattern) or level 2 (principle) based on
    category diversity.

    Returns a dict ready to be appended to the lessons store.
    """
    if not lessons_batch:
        raise ValueError("lessons_batch must contain at least one lesson")

    # Gather text and categories
    texts = [l["text"] for l in lessons_batch]
    categories = {l.get("category", "uncategorized") for l in lessons_batch}

    # Very simple keyword extraction – most common non‑stop words
    stop_words = {"the", "and", "to", "of", "a", "in", "for", "on", "with", "is"}
    word_counter = Counter()
    for txt in texts:
        for w in txt.lower().split():
            w_clean = "".join(ch for ch in w if ch.isalnum())
            if w_clean and w_clean not in stop_words:
                word_counter[w_clean] += 1
    top_keywords = [w for w, _ in word_counter.most_common(5)]

    # Build a concise reflection sentence
    summary = f"Observed pattern: {' , '.join(top_keywords)}."
    if len(categories) > 1:
        summary = "Principle derived: " + summary

    # Determine level
    level = 2 if len(categories) > 1 else 1

    # Importance of the reflection is the max of its constituents
    importance = max(compute_importance(l) for l in lessons_batch)

    reflection = {
        "text": summary,
        "category": " / ".join(sorted(categories)),
        "retrieval_count": 0,
        "last_retrieved": _now_iso(),
        "impact": importance,
        "level": level,
        "derived_from": [l.get("id") for l in lessons_batch if "id" in l],
        "created_at": _now_iso(),
    }
    return reflection


def prune_redundant(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove lessons that are subsumed by higher‑level reflections.
    A lesson is considered redundant if:
        * it is level 0 (raw) and its text appears verbatim in a level ≥1 entry,
        * or its importance score is below a small threshold (0.15) and it has
          not been retrieved in the last 60 days.
    Returns a new list with the kept lessons.
    """
    # Build quick lookup of higher‑level texts
    higher_texts = {
        l["text"] for l in lessons if l.get("level", 0) >= 1
    }

    pruned = []
    for l in lessons:
        if l.get("level", 0) == 0 and l["text"] in higher_texts:
            continue  # subsumed
        # Recency check
        try:
            last = datetime.datetime.fromisoformat(
                l.get("last_retrieved", "1970-01-01T00:00:00Z".replace("Z", ""))
            )
        except ValueError:
            last = datetime.datetime(1970, 1, 1)
        days_since = (datetime.datetime.utcnow() - last).days
        imp = compute_importance(l)
        if imp < 0.15 and days_since > 60:
            continue  # archive
        pruned.append(l)
    return pruned


# --------------------------------------------------------------------------- #
# Periodic synthesis driver
# --------------------------------------------------------------------------- #
def run_periodic_synthesis(session_counter: int) -> None:
    """
    Called after each grind session. When ``session_counter`` reaches a multiple
    of 10 the synthesis pipeline runs:
        1. Load all lessons.
        2. Score importance and promote frequently‑retrieved lessons.
        3. Identify patterns (≥3 occurrences) → generate level‑1 reflections.
        4. Identify cross‑category patterns → generate level‑2 principles.
        5. Prune redundant entries.
        6. Append new reflections to the JSON store.
    """
    if session_counter % 10 != 0:
        return  # No synthesis this round

    lessons = load_all_lessons()

    # ---- 1. Score importance & promote ----
    for l in lessons:
        l["importance"] = compute_importance(l)
        # Promote if importance > 0.7 and currently raw
        if l["importance"] > 0.7 and l.get("level", 0) == 0:
            l["level"] = 1

    # ---- 2. Find patterns (raw lessons appearing >=3 times) ----
    text_counter = Counter(l["text"] for l in lessons if l.get("level", 0) == 0)
    pattern_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for l in lessons:
        if l.get("level", 0) == 0 and text_counter[l["text"]] >= 3:
            pattern_groups[l["text"]].append(l)

    new_reflections: List[Dict[str, Any]] = []
    for _, batch in pattern_groups.items():
        reflection = generate_reflection(batch)
        new_reflections.append(reflection)

    # ---- 3. Find cross‑category patterns for principles ----
    # Group by category pairs that share at least 3 lessons each
    cat_to_lessons: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for l in lessons:
        if l.get("level", 0) == 0:
            cat_to_lessons[l.get("category", "uncategorized")].append(l)

    # Simple heuristic: if total raw lessons across >1 category >=5, synthesize principle
    multi_cat_lessons = [
        l for l in lessons if l.get("level", 0) == 0 and len(cat_to_lessons) > 1
    ]
    if len(multi_cat_lessons) >= 5:
        principle = generate_reflection(multi_cat_lessons)
        principle["level"] = 2
        new_reflections.append(principle)

    # ---- 4. Prune redundant entries ----
    updated_lessons = prune_redundant(lessons + new_reflections)

    # Remove temporary fields before persisting
    for l in updated_lessons:
        l.pop("importance", None)

    # Persist
    _dump_json(updated_lessons, LESSONS_PATH)


# --------------------------------------------------------------------------- #
# If executed as a script, run a demo synthesis based on a dummy counter.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Example usage: pretend we have just finished the 10th session.
    run_periodic_synthesis(session_counter=10)
    print(f"Synthesis completed. Updated lessons stored at {LESSONS_PATH}")