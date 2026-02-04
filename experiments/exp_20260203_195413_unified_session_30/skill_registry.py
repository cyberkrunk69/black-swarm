import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# ----------------------------------------------------------------------
# Helper functions for embedding handling
# ----------------------------------------------------------------------
def compute_embedding(skills):
    """
    Compute a TF‑IDF based embedding for each skill description.

    Parameters
    ----------
    skills : dict
        Mapping of skill_id -> description string.

    Returns
    -------
    np.ndarray
        2‑D array where each row is the normalized TF‑IDF vector for a skill.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(list(skills.values()))
    # TF‑IDF from sklearn is already L2‑normalized per row.
    return tfidf_matrix.toarray()


def semantic_search(query, skills, embeddings, top_k=3):
    """
    Retrieve the most semantically similar skills to a free‑text query.

    Parameters
    ----------
    query : str
        User query.
    skills : dict
        Mapping of skill_id -> description.
    embeddings : np.ndarray
        Pre‑computed skill embeddings (rows correspond to ``skills`` order).
    top_k : int, optional
        Number of results to return (default 3).

    Returns
    -------
    list[str]
        List of skill IDs ordered by decreasing similarity.
    """
    # Build a TF‑IDF vector for the query using the same vocabulary as the skill embeddings.
    # To guarantee the same feature space we reuse the vectorizer that produced the skill embeddings.
    # For simplicity we fit a new vectorizer on the query + all skill texts; the resulting
    # vector will be compatible because the TF‑IDF vectors are L2‑normalized.
    vectorizer = TfidfVectorizer()
    # Fit on the union of skill texts and the query to keep vocab consistent.
    vectorizer.fit(list(skills.values()) + [query])
    query_vec = vectorizer.transform([query]).toarray()

    # Compute cosine similarity (dot product because vectors are L2‑normalized)
    sims = cosine_similarity(query_vec, embeddings).flatten()
    top_indices = np.argsort(-sims)[:top_k]
    skill_ids = list(skills.keys())
    return [skill_ids[i] for i in top_indices]


# ----------------------------------------------------------------------
# Core class handling skill retrieval
# ----------------------------------------------------------------------
class SkillRegistry:
    """
    Manages a library of skills and provides both keyword‑based and
    embedding‑based retrieval.
    """

    def __init__(self, skill_file_path):
        """
        Load skills from ``skill_file_path`` (JSON) and compute embeddings.

        The JSON file is expected to have the structure:
        {
            "skills": {
                "skill_id_1": "description ...",
                "skill_id_2": "description ..."
            }
        }
        """
        self.skill_file_path = skill_file_path
        self._load_skills()
        self.embeddings = compute_embedding(self.skills)

        # Persist embeddings alongside the original data for future runs
        self._persist_library()

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------
    def _load_skills(self):
        """Read the JSON skill library."""
        if not os.path.isfile(self.skill_file_path):
            raise FileNotFoundError(f"Skill library not found: {self.skill_file_path}")

        with open(self.skill_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Expect a top‑level key "skills"
        self.skills = data.get("skills", {})
        if not isinstance(self.skills, dict):
            raise ValueError("Invalid skill library format – expected a dict under 'skills'.")

    def _persist_library(self):
        """Write the skill library back, now including the embeddings."""
        # Convert numpy array to list for JSON serialisation
        emb_list = self.embeddings.tolist()
        payload = {
            "skills": self.skills,
            "embeddings": emb_list
        }
        with open(self.skill_file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Retrieval API
    # ------------------------------------------------------------------
    def retrieve_skill(self, query, top_k=3):
        """
        Attempt keyword‑based retrieval first; if no exact keyword match is found,
        fall back to semantic similarity search.

        Parameters
        ----------
        query : str
            The user query.
        top_k : int, optional
            Number of results for the semantic fallback (default 3).

        Returns
        -------
        list[str]
            List of matching skill IDs.
        """
        # Simple keyword match (case‑insensitive substring search)
        keyword_matches = [
            skill_id
            for skill_id, description in self.skills.items()
            if query.lower() in description.lower()
        ]

        if keyword_matches:
            return keyword_matches

        # No direct keyword hits → use embedding similarity
        return semantic_search(query, self.skills, self.embeddings, top_k=top_k)


# ----------------------------------------------------------------------
# Example usage (can be removed or guarded by __name__ == "__main__")
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Path is relative to the workspace root; adjust as needed.
    skill_json_path = os.path.join(
        os.path.dirname(__file__), "..", "skill_library.json"
    )
    registry = SkillRegistry(skill_json_path)

    test_queries = [
        "python",          # direct keyword match
        "machine learning",  # likely semantic match
        "frontend",       # may fall back to semantic
    ]

    for q in test_queries:
        matches = registry.retrieve_skill(q)
        print(f"Query: '{q}' → Matches: {matches}")