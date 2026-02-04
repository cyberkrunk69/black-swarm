"""
Utility helpers for dealing with embeddings used by the cache system.

The real implementation would call a model (e.g. OpenAI, Sentence‑Transformers) to
produce a dense vector representation of a piece of text.  For the purpose of
this repository a stub that returns a deterministic random vector is provided.
"""

import hashlib
import numpy as np
from typing import Iterable, List


def _seed_from_text(text: str) -> int:
    """Create a reproducible integer seed from arbitrary text."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)


def embed_text(text: str, dim: int = 384) -> np.ndarray:
    """
    Generate a deterministic pseudo‑embedding for *text*.

    In production this would forward the text to a language model.  Here we
    generate a pseudo‑random vector seeded by the text so that identical inputs
    always produce identical embeddings.

    Parameters
    ----------
    text: str
        The text to embed.
    dim: int, optional
        Dimensionality of the embedding vector (default: 384).

    Returns
    -------
    np.ndarray
        Normalised embedding vector.
    """
    rng = np.random.default_rng(_seed_from_text(text))
    vec = rng.normal(size=dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def batch_embed_texts(texts: Iterable[str], dim: int = 384) -> List[np.ndarray]:
    """
    Embed an iterable of strings, returning a list of normalised vectors.
    """
    return [embed_text(t, dim=dim) for t in texts]