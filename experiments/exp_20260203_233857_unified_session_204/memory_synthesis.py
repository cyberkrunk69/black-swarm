import json
import os
import math
import re
from collections import Counter
from typing import List, Dict, Tuple

# ----------------------------------------------------------------------
# Helper functions for text processing and simple TF‑IDF style embeddings
# ----------------------------------------------------------------------
def _normalize_text(text: str) -> str:
    """Lower‑case and remove non‑alphanumeric characters."""
    return re.sub(r'[^a-z0-9\s]', ' ', text.lower())

def compute_lesson_embedding(lesson_text: str) -> Dict[str, float]:
    """
    Create a very lightweight TF‑IDF‑style embedding.

    Steps:
        1. Normalize the text.
        2. Tokenize on whitespace.
        3. Count term frequencies.
        4. Convert counts to L2‑normalized float weights.

    Returns a dictionary mapping term → weight.
    """
    normalized = _normalize_text(lesson_text)
    tokens = normalized.split()
    if not tokens:
        return {}

    term_counts = Counter(tokens)
    # L2‑norm for simple similarity
    norm = math.sqrt(sum(cnt * cnt for cnt in term_counts.values()))
    return {term: cnt / norm for term, cnt in term_counts.items()}

def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vectors."""
    if not vec_a or not vec_b:
        return 0.0
    # dot product
    dot = sum(vec_a.get(k, 0.0) * v for k, v in vec_b.items())
    # norms are already baked into the vectors (they are L2‑normalized)
    # therefore similarity = dot product
    return dot

def retrieve_relevant_lessons(
    query: str,
    lessons: List[Dict],
    top_k: int = 5
) -> List[Dict]:
    """
    Rank lessons by a blend of their stored importance and semantic similarity
    to the query.

    Scoring formula:
        score = (importance * 0.4) + (embedding_similarity * 0.6)

    Returns the top‑k lesson dictionaries.
    """
    query_emb = compute_lesson_embedding(query)

    scored_lessons: List[Tuple[float, Dict]] = []
    for lesson in lessons:
        # Expected lesson dict shape:
        # {
        #   "text": "...",
        #   "importance": float,
        #   ... (other fields)
        # }
        lesson_text = lesson.get("text", "")
        lesson_importance = float(lesson.get("importance", 0.0))

        lesson_emb = compute_lesson_embedding(lesson_text)
        similarity = _cosine_similarity(query_emb, lesson_emb)

        score = (lesson_importance * 0.4) + (similarity * 0.6)
        scored_lessons.append((score, lesson))

    # Sort descending by score and slice top_k
    scored_lessons.sort(key=lambda x: x[0], reverse=True)
    return [lesson for _, lesson in scored_lessons[:top_k]]

# ----------------------------------------------------------------------
# Core synthesis logic (existing functionality enhanced with semantic retrieval)
# ----------------------------------------------------------------------
def synthesize(memory_path: str, reflection_query: str) -> Dict:
    """
    Main entry point for the memory synthesis process.

    Parameters
    ----------
    memory_path : str
        Path to the JSON file containing stored lessons.
    reflection_query : str
        The current query/goal for which we want to reflect on past lessons.

    Returns
    -------
    Dict
        A dictionary containing the synthesized reflection and the lessons
        that contributed to it.
    """
    # Load existing lessons
    if not os.path.exists(memory_path):
        raise FileNotFoundError(f"Memory file not found: {memory_path}")

    with open(memory_path, "r", encoding="utf-8") as f:
        all_lessons = json.load(f)

    # ------------------------------------------------------------------
    # 1️⃣  Semantic retrieval of the most relevant lessons
    # ------------------------------------------------------------------
    relevant_lessons = retrieve_relevant_lessons(
        query=reflection_query,
        lessons=all_lessons,
        top_k=5
    )

    # ------------------------------------------------------------------
    # 2️⃣  Simple importance‑based aggregation (preserve original behaviour)
    # ------------------------------------------------------------------
    # The original code weighted lessons by their stored importance.
    # We'll keep that logic but now only over the retrieved subset.
    total_importance = sum(float(l.get("importance", 0.0)) for l in relevant_lessons) or 1.0

    weighted_summary = ""
    for lesson in relevant_lessons:
        weight = float(lesson.get("importance", 0.0)) / total_importance
        weighted_summary += f"[Weight {weight:.2f}] {lesson.get('text', '')}\n"

    # ------------------------------------------------------------------
    # 3️⃣  Build the final reflection output
    # ------------------------------------------------------------------
    reflection = {
        "query": reflection_query,
        "selected_lessons": [l.get("text", "") for l in relevant_lessons],
        "weighted_summary": weighted_summary.strip(),
        "timestamp": None  # placeholder – can be filled by caller if needed
    }

    # ------------------------------------------------------------------
    # 4️⃣  Persist the selected lessons back to the learned lessons file
    # ------------------------------------------------------------------
    learned_path = os.path.join(
        os.path.dirname(memory_path),
        "learned_lessons.json"
    )
    try:
        if os.path.exists(learned_path):
            with open(learned_path, "r", encoding="utf-8") as f:
                learned = json.load(f)
        else:
            learned = []
    except json.JSONDecodeError:
        learned = []

    # Append only the lesson *objects* (preserve importance etc.)
    learned.extend(relevant_lessons)

    with open(learned_path, "w", encoding="utf-8") as f:
        json.dump(learned, f, ensure_ascii=False, indent=2)

    return reflection

# ----------------------------------------------------------------------
# If this module is executed directly, run a tiny demo (optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Demo usage – assumes a `memory.json` file exists next to this script.
    demo_memory = os.path.join(os.path.dirname(__file__), "memory.json")
    demo_query = "How can I improve my code review process?"
    result = synthesize(demo_memory, demo_query)
    print(json.dumps(result, indent=2, ensure_ascii=False))