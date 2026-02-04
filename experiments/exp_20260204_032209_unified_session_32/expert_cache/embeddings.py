"""
Minimal embedding utilities.

In a real deployment this would call a vector model (e.g., OpenAI,
Sentence‑Transformers, etc.). For the purpose of the experiment we
provide a deterministic, lightweight fallback based on TF‑IDF‑like
hashing.
"""

import hashlib
import numpy as np
from typing import List

def _text_to_vector(text: str, dim: int = 128) -> np.ndarray:
    """Deterministic pseudo‑embedding: hash the text and expand to a fixed‑size vector."""
    # Produce a reproducible 256‑bit digest
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Convert to uint8 array then to float32
    arr = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
    # Pad / truncate to required dimension
    if dim > arr.size:
        arr = np.pad(arr, (0, dim - arr.size), mode="wrap")
    else:
        arr = arr[:dim]
    # Normalise to unit length for cosine similarity
    norm = np.linalg.norm(arr)
    return arr / norm if norm > 0 else arr

def embed_text(texts: List[str], dim: int = 128) -> np.ndarray:
    """
    Convert a list of strings to a (N, dim) matrix of embeddings.
    """
    vectors = [_text_to_vector(t, dim) for t in texts]
    return np.stack(vectors, axis=0)