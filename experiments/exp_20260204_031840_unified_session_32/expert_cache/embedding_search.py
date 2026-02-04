"""
Utility functions for generating embeddings and performing semantic similarity
search within the cache.
"""

from typing import List, Tuple
import numpy as np

# The actual embedding model will be lazily loaded the first time it is needed.
# This keeps import time low and allows the surrounding environment to provide
# any required heavy dependencies (e.g., torch, transformers).
_model = None


def _load_model():
    """Load the embedding model defined in config."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        from .config import EMBEDDING_MODEL_NAME

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Convert a list of strings to a 2‑D NumPy array of embeddings.

    Args:
        texts: List of strings to embed.

    Returns:
        np.ndarray of shape (len(texts), embedding_dim)
    """
    model = _load_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return np.asarray(embeddings, dtype=np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between two matrices.

    Args:
        a: (N, D) matrix.
        b: (M, D) matrix.

    Returns:
        (N, M) similarity matrix.
    """
    # Both a and b are expected to be L2‑normalized.
    return np.dot(a, b.T)


def top_k_similar(
    query_embedding: np.ndarray,
    candidate_embeddings: np.ndarray,
    k: int = 5,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Return indices and similarity scores of the top‑k most similar candidates.

    Args:
        query_embedding: (D,) vector (already normalized).
        candidate_embeddings: (N, D) matrix (already normalized).
        k: Number of results to return.

    Returns:
        (indices, scores) where indices.shape == (k,) and scores.shape == (k,).
    """
    if candidate_embeddings.shape[0] == 0:
        return np.array([], dtype=int), np.array([], dtype=float)

    sims = cosine_similarity(query_embedding[None, :], candidate_embeddings).flatten()
    top_idx = np.argpartition(-sims, min(k, len(sims) - 1))[:k]
    # Sort the top indices by actual similarity descending
    sorted_order = np.argsort(-sims[top_idx])
    top_idx = top_idx[sorted_order]
    return top_idx, sims[top_idx]