import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
BASE_DIR = "/app"
LESSONS_PATH = os.path.join(BASE_DIR, "learned_lessons.json")
SYNTHESIS_BATCH_SIZE = 10  # number of sessions after which synthesis runs
PATTERN_THRESHOLD = 3      # occurrences needed to promote to a pattern (Level 1)
IMPORTANCE_WEIGHTS = {
    "retrieval": 0.5,
    "recency": 0.3,
    "impact": 0.2,
}
# ----------------------------------------------------------------------


def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _dump_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_all_lessons() -> List[Dict[str, Any]]:
    """
    Load all lessons from the persistent storage.
    Returns a flat list of lesson dictionaries.
    """
    lessons = _load_json(LESSONS_PATH)
    if not isinstance(lessons, list):
        lessons = []
    return lessons


def compute_importance(lesson: Dict[str, Any]) -> float:
    """
    Compute an importance score for a lesson based on:
      - retrieval frequency
      - recency (how recent it was accessed)
      - impact (a user‑provided scalar)
    """
    retrieval = lesson.get("retrieval_count", 0)
    impact = lesson.get("impact", 0.0)

    # Recency: days since last accessed (more recent -> higher score)
    last_ts = lesson.get("last_accessed")
    if last_ts:
        try:
            last_dt = datetime.fromisoformat(last_ts)
            days_ago = (datetime.utcnow() - last_dt).days
            recency_score = max(0.0, 1.0 - days_ago / 365.0)  # linear decay over a year
        except Exception:
            recency_score = 0.0
    else:
        recency_score = 0.0

    # Weighted sum
    score = (
        IMPORTANCE_WEIGHTS["retrieval"] * retrieval
        + IMPORTANCE_WEIGHTS["recency"] * recency_score
        + IMPORTANCE_WEIGHTS["impact"] * impact
    )
    return score


def generate_reflection(lessons_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize a higher‑level insight from a batch of lessons.
    Returns a new lesson dict representing the reflection.
    """
    if not lessons_batch:
        return {}

    # Gather common words/phrases (very naive approach)
    all_text = " ".join(l["lesson"] for l in lessons_batch if "lesson" in l)
    words = [w.lower().strip('.,!?:;') for w in all_text.split()]
    common = [w for w, cnt in Counter(words).items() if cnt >= 2]

    # Build a concise reflection
    reflection_text = (
        "When " + ", ".join(common[:3]) + ", it often leads to "
        + "better outcomes across contexts."
    ) if common else "A recurring insight emerged from recent experiences."

    # Aggregate metadata
    avg_impact = sum(l.get("impact", 0) for l in lessons_batch) / len(lessons_batch)
    max_retrieval = max(l.get("retrieval_count", 0) for l in lessons_batch)

    reflection = {
        "lesson": reflection_text,
        "category": "reflection",
        "level": determine_level(lessons_batch),
        "retrieval_count": max_retrieval,
        "last_accessed": datetime.utcnow().isoformat(),
        "impact": round(avg_impact, 2),
        "source_lessons": [l.get("lesson") for l in lessons_batch],
    }
    return reflection


def prune_redundant(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove lessons that are effectively subsumed by higher‑level reflections.
    A lesson is considered redundant if its text appears as a substring
    of any reflection's text.
    """
    reflections = [l for l in lessons if l.get("level", 0) > 0]
    reflection_texts = [r["lesson"] for r in reflections]

    pruned = []
    for lesson in lessons:
        text = lesson.get("lesson", "")
        if any(text in refl for refl in reflection_texts):
            continue  # redundant
        pruned.append(lesson)
    return pruned


def determine_level(lessons_batch: List[Dict[str, Any]]) -> int:
    """
    Determine the hierarchical level for a synthesized lesson.
    Level 0: raw observations
    Level 1: patterns (appear >= PATTERN_THRESHOLD)
    Level 2: principles (span multiple categories)
    """
    # Count categories in the batch
    categories = {l.get("category") for l in lessons_batch}
    if len(categories) > 1:
        return 2  # principle
    # Check frequency of identical lesson texts
    texts = [l.get("lesson") for l in lessons_batch]
    most_common, freq = Counter(texts).most_common(1)[0] if texts else (None, 0)
    if freq >= PATTERN_THRESHOLD:
        return 1  # pattern
    return 0  # raw observation (fallback)


def promote_lessons(lessons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Promote frequently retrieved lessons to higher hierarchical levels.
    """
    # Group by lesson text
    lesson_groups = defaultdict(list)
    for l in lessons:
        lesson_groups[l["lesson"]].append(l)

    new_lessons = lessons.copy()
    for text, group in lesson_groups.items():
        total_retrieval = sum(g.get("retrieval_count", 0) for g in group)
        if total_retrieval >= 10:  # arbitrary promotion threshold
            # Create a pattern reflection if not already present
            existing = any(
                l for l in new_lessons if l.get("lesson") == text and l.get("level", 0) >= 1
            )
            if not existing:
                reflection = generate_reflection(group)
                new_lessons.append(reflection)
    return new_lessons


def archive_unused(lessons: List[Dict[str, Any]], days_unused: int = 30) -> List[Dict[str, Any]]:
    """
    Remove lessons that haven't been accessed for `days_unused` days.
    """
    cutoff = datetime.utcnow() - timedelta(days=days_unused)
    kept = []
    for l in lessons:
        last = l.get("last_accessed")
        if not last:
            kept.append(l)
            continue
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt >= cutoff:
                kept.append(l)
        except Exception:
            kept.append(l)
    return kept


def periodic_synthesis(session_counter: int) -> None:
    """
    Run synthesis after every SYNTHESIS_BATCH_SIZE grind sessions.
    This function updates the persistent lesson store.
    """
    if session_counter % SYNTHESIS_BATCH_SIZE != 0:
        return

    lessons = load_all_lessons()
    if not lessons:
        return

    # Compute importance scores
    for l in lessons:
        l["importance"] = compute_importance(l)

    # Sort by importance descending
    lessons.sort(key=lambda x: x.get("importance", 0), reverse=True)

    # Take top N lessons for synthesis (N can be tuned)
    top_batch = lessons[:min(20, len(lessons))]

    # Generate a reflection from the batch
    reflection = generate_reflection(top_batch)
    if reflection:
        lessons.append(reflection)

    # Promote frequently retrieved lessons
    lessons = promote_lessons(lessons)

    # Prune redundant entries
    lessons = prune_redundant(lessons)

    # Archive rarely used lessons
    lessons = archive_unused(lessons)

    # Clean up temporary fields
    for l in lessons:
        l.pop("importance", None)

    _dump_json(lessons, LESSONS_PATH)


# ----------------------------------------------------------------------
# Helper for external modules
# ----------------------------------------------------------------------
def run_synthesis_if_needed(session_counter: int) -> None:
    """
    Public entry point used by the grind loop or other orchestrators.
    """
    periodic_synthesis(session_counter)


# ----------------------------------------------------------------------
# If executed directly, perform a demo run (useful for testing)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Simulate a call after 10 sessions
    demo_counter = 10
    print(f"Running memory synthesis for session count {demo_counter}...")
    run_synthesis_if_needed(demo_counter)
    print("Synthesis complete.")