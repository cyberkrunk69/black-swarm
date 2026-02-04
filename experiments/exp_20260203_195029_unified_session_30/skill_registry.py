import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------------------------------------------------
# Load existing skill library (if present) or fall back to a placeholder.
# ----------------------------------------------------------------------
SKILL_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "skill_library.json")

if os.path.exists(SKILL_LIBRARY_PATH):
    with open(SKILL_LIBRARY_PATH, "r") as f:
        data = json.load(f)
        skill_library = data.get("skills", {})
        stored_embeddings = data.get("embeddings", {})
else:
    # Placeholder skill set – replace with the real data in production.
    skill_library = {
        "skill1": "This is a sample skill for demonstration purposes.",
        "skill2": "Another example skill to show the functionality.",
        "skill3": "A third skill to test the semantic search."
    }
    stored_embeddings = {}

# ----------------------------------------------------------------------
# Embedding utilities
# ----------------------------------------------------------------------
_vectorizer = TfidfVectorizer()

def _fit_vectorizer(skills):
    """Fit the TF‑IDF vectorizer on the full set of skill descriptions."""
    descriptions = list(skills.values())
    _vectorizer.fit(descriptions)

def compute_embedding(text):
    """
    Compute a normalized TF‑IDF embedding for a single piece of text.
    Returns a 1‑D NumPy array.
    """
    tfidf = _vectorizer.transform([text])
    vec = tfidf.toarray()[0]
    norm = np.linalg.norm(vec)
    return vec / norm if norm != 0 else vec

# ----------------------------------------------------------------------
# Semantic search
# ----------------------------------------------------------------------
def semantic_search(query, skills, top_k=3):
    """
    Return the `top_k` skill keys whose descriptions are most similar
    to `query` using cosine similarity over TF‑IDF embeddings.
    """
    # Ensure the vectorizer knows about all skill texts
    _fit_vectorizer(skills)

    query_emb = compute_embedding(query)

    # Compute embeddings for all skills (reuse stored ones when possible)
    skill_embeddings = {}
    for name, desc in skills.items():
        if name in stored_embeddings:
            emb = np.array(stored_embeddings[name])
        else:
            emb = compute_embedding(desc)
            stored_embeddings[name] = emb.tolist()   # cache for later persistence
        skill_embeddings[name] = emb

    # Cosine similarity between query and each skill
    sims = {
        name: cosine_similarity([query_emb], [emb])[0][0]
        for name, emb in skill_embeddings.items()
    }

    # Sort by similarity descending and return top_k keys
    ranked = sorted(sims, key=sims.get, reverse=True)[:top_k]
    return ranked

# ----------------------------------------------------------------------
# Retrieval entry point
# ----------------------------------------------------------------------
def retrieve_skill(query, skills=None, top_k=3):
    """
    Primary skill lookup. First attempts a simple keyword match;
    if none are found, falls back to semantic search.
    """
    if skills is None:
        skills = skill_library

    # Keyword‑based fallback (case‑insensitive substring search)
    keyword_hits = [
        name for name, desc in skills.items()
        if query.lower() in desc.lower()
    ]

    if keyword_hits:
        return keyword_hits[:top_k]

    # No direct keyword hits → semantic search
    return semantic_search(query, skills, top_k=top_k)

# ----------------------------------------------------------------------
# Persist embeddings alongside the skill definitions
# ----------------------------------------------------------------------
def _persist_library():
    payload = {
        "skills": skill_library,
        "embeddings": stored_embeddings
    }
    with open(SKILL_LIBRARY_PATH, "w") as f:
        json.dump(payload, f, indent=2)

# Persist on module load so that new embeddings are saved after the first call.
_persist_library()

# ----------------------------------------------------------------------
# Example usage (can be removed in production)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    test_query = "sample skill"
    print("Query:", test_query)
    print("Result:", retrieve_skill(test_query))