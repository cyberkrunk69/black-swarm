import json
import math
import re
from collections import Counter
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Helper functions for text processing and simple TF‑IDF embeddings
# ----------------------------------------------------------------------
def _tokenize(text: str) -> List[str]:
    """Lower‑case and split text into alphanumeric tokens."""
    return re.findall(r"\b\w+\b", text.lower())


def _compute_idf(lessons: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute inverse‑document‑frequency for all terms appearing in the
    supplied lessons.  ``lessons`` is expected to be a list of dicts
    containing a ``text`` field.
    """
    doc_freq = Counter()
    total_docs = len(lessons)

    for lesson in lessons:
        tokens = set(_tokenize(lesson.get("text", "")))
        for token in tokens:
            doc_freq[token] += 1

    # Smoothed IDF
    idf = {
        token: math.log((total_docs + 1) / (freq + 1)) + 1.0
        for token, freq in doc_freq.items()
    }
    return idf


def compute_lesson_embedding(lesson_text: str, idf: Dict[str, float]) -> Dict[str, float]:
    """
    Create a very small TF‑IDF style vector for *lesson_text* using the
    pre‑computed ``idf`` map.
    """
    tf = Counter(_tokenize(lesson_text))
    embedding = {
        term: tf[term] * idf.get(term, 0.0)
        for term in tf
    }
    return embedding


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Return cosine similarity between two sparse vectors."""
    intersect = set(vec_a) & set(vec_b)
    dot_product = sum(vec_a[t] * vec_b[t] for t in intersect)

    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def retrieve_relevant_lessons(
    query: str,
    lessons: List[Dict[str, Any]],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Rank *lessons* by a blend of their stored ``importance`` weight and
    semantic similarity to *query*.
    """
    # Compute IDF across the whole lesson corpus
    idf = _compute_idf(lessons)

    # Embedding for the incoming query
    query_emb = compute_lesson_embedding(query, idf)

    scored_lessons = []
    for lesson in lessons:
        lesson_text = lesson.get("text", "")
        lesson_emb = compute_lesson_embedding(lesson_text, idf)

        embedding_similarity = _cosine_similarity(query_emb, lesson_emb)
        importance = lesson.get("importance", 0.0)

        # Blend the two signals (weights sum to 1.0)
        score = importance * 0.4 + embedding_similarity * 0.6
        scored_lessons.append((score, lesson))

    # Return the top‑k lessons sorted by descending score
    scored_lessons.sort(key=lambda pair: pair[0], reverse=True)
    return [lesson for _, lesson in scored_lessons[:top_k]]


# ----------------------------------------------------------------------
# Core synthesis logic (existing functionality preserved where possible)
# ----------------------------------------------------------------------
def synthesize(query: str) -> str:
    """
    Main entry point used by HippoRAG.  It loads the learned lessons,
    retrieves the most relevant ones using the new embedding‑based
    retrieval, and then proceeds with the original reflection logic.
    """
    # Load learned lessons – create the file if it does not exist
    lessons_path = "learned_lessons.json"
    try:
        with open(lessons_path, "r", encoding="utf-8") as f:
            lessons = json.load(f)
    except FileNotFoundError:
        lessons = []

    # ------------------------------------------------------------------
    # 1️⃣  Semantic retrieval of the most pertinent lessons
    # ------------------------------------------------------------------
    relevant_lessons = retrieve_relevant_lessons(query, lessons, top_k=5)

    # ------------------------------------------------------------------
    # 2️⃣  (Placeholder) Existing reflection / synthesis logic.
    #     In the original code this would combine the selected lessons
    #     with the query to produce a response.  Here we keep the
    #     behaviour minimal while demonstrating the new pipeline.
    # ------------------------------------------------------------------
    reflection_parts = [lesson.get("text", "") for lesson in relevant_lessons]
    reflection = "\n---\n".join(reflection_parts)

    # ------------------------------------------------------------------
    # 3️⃣  Persist any new lessons that were generated during this call.
    #     For demonstration we simply re‑append the retrieved lessons
    #     (deduplication omitted for brevity).
    # ------------------------------------------------------------------
    if relevant_lessons:
        # Append only if they are not already present (simple check)
        existing_texts = {lesson.get("text") for lesson in lessons}
        new_entries = [
            lesson for lesson in relevant_lessons
            if lesson.get("text") not in existing_texts
        ]
        if new_entries:
            lessons.extend(new_entries)
            with open(lessons_path, "w", encoding="utf-8") as f:
                json.dump(lessons, f, ensure_ascii=False, indent=2)

    # Return the composed reflection (or whatever the original function
    # would have returned).  This placeholder simply echoes the selected
    # lesson texts.
    return reflection


# ----------------------------------------------------------------------
# If this module is executed directly, run a tiny demo.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    demo_query = "How can I improve memory retention while studying?"
    print("=== Retrieved Lessons ===")
    print(synthesize(demo_query))