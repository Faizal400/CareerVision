# src/core_engine/semantic_similarity.py
"""
Document-level semantic similarity (CV ↔ JD) using sentence-transformers.

Important design choice:
- We use embeddings ONLY for semantic similarity of whole documents/sections.
- We do NOT use embeddings to "extract skills" from ESCO labels, because that caused
  massive false positives and undermined trust in outputs.

If sentence-transformers is not installed, this module returns 0.0 and the system
still works (TF-IDF + skill features).
"""

from __future__ import annotations

from django.core.cache import cache

MODEL_NAME = "all-MiniLM-L6-v2"


def _lazy_import():
    from sentence_transformers import SentenceTransformer
    import numpy as np
    return SentenceTransformer, np


def _get_model():
    cached = cache.get("cv_jd_semantic_model")
    if cached is not None:
        return cached
    SentenceTransformer, _ = _lazy_import()
    model = SentenceTransformer(MODEL_NAME)
    cache.set("cv_jd_semantic_model", model, timeout=None)
    return model


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Return cosine similarity mapped to [0, 1].

    Inputs: two strings
    Output: float in [0, 1]
    Failure cases:
      - empty strings -> 0.0
      - missing dependency -> 0.0
    """
    if not text_a or not text_b:
        return 0.0

    try:
        model = _get_model()
        # normalize_embeddings=True gives unit vectors; dot product == cosine
        vecs = model.encode([text_a, text_b], normalize_embeddings=True)
        # vecs can be numpy array-like
        score = float(vecs[0] @ vecs[1])
        # score is typically in [-1, 1]; map to [0, 1]
        mapped = (score + 1.0) / 2.0
        return max(0.0, min(1.0, mapped))
    except Exception:
        # Safe fallback: system still functions on TF-IDF + skills
        print("Warning: semantic similarity computation failed (missing dependency or other error). Returning 0.0.")
        return 0.0
