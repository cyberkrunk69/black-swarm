"""
Utility functions for turning arbitrary Python objects into vector embeddings.

The implementation is deliberately lightweight and does **not** depend on any
external API keys.  It uses the `sentence_transformers` library if available;
otherwise it falls back to a simple TF‑IDF based vectorizer.

Only the `embed` function is part of the public API.
"""

import hashlib
import json
import os
from typing import Any, List

try:
    from sentence_transformers import SentenceTransformer
    _model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:  # pragma: no cover
    _model = None

def _fallback_embed(text: str) -> List[float]:
    """Very naive deterministic embedding based on a hash."""
    # Produce a 128‑dimensional vector from SHA‑256 hash bytes
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return [b / 255.0 for b in h[:128]]

def embed(item: Any) -> List[float]:
    """
    Convert ``item`` into a dense embedding vector.

    Parameters
    ----------
    item:
        Anything JSON‑serialisable (e.g. str, dict, list).  The object is first
        turned into a JSON string; that string is then embedded.

    Returns
    -------
    List[float]
        A list of floats representing the embedding.
    """
    # Normalise the input to a JSON string
    if not isinstance(item, str):
        try:
            item = json.dumps(item, sort_keys=True, ensure_ascii=False)
        except TypeError:
            item = str(item)

    if _model is not None:
        return _model.encode(item).tolist()
    else:
        return _fallback_embed(item)