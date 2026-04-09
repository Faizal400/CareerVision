# core_engine/embeddings.py
"""
Layer 3: Semantic skill matching using sentence-transformers.

Complements keyword matching (layers 1+2) by matching on meaning,
not exact words. "build REST services" matches "REST API" even though
the words differ.
"""

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.core.cache import cache


MODEL_NAME = "all-MiniLM-L6-v2"  # 90MB, fast, good for short texts
SIMILARITY_THRESHOLD = 0.35 # a higher number means more similar. Tune this based on testing with real CVs/JDs. 0.6-0.7 is a common range for semantic similarity.





def _get_model() -> SentenceTransformer:
    """Load model once and cache in memory."""
    cached = cache.get("SentenceTransformerModel")
    if cached is not None:
        return cached
    model = SentenceTransformer(MODEL_NAME)
    cache.set("SentenceTransformerModel", model, timeout=None)
    return model

def _get_skill_vectors() -> tuple[list[str], np.ndarray]:
    """
    Encode all ESCO skill labels once and cache.
    Returns (list of skill labels, matrix of vectors)
    """
    # not familiar with some syntax + forgot some
    cached = cache.get("ESCOSkillsVectors")
    if cached is not None:
        return cached
    sBTModel = _get_model()
    from career_explorer.models import ESCOSkill
    AllSkills = ESCOSkill.objects.all() # get all skills
    labels = [s.skill_label for s in AllSkills]
    vectors = sBTModel.encode(labels)
    result = (labels, vectors)
    cache.set("ESCOSkillsVectors", result, timeout=None)
    return result

def extract_skills_semantic(text: str) -> set[str]:
    """
    Given a block of text, return skill labels whose meaning
    is semantically similar to the text.

    Inputs:  raw text string (CV or JD)
    Outputs: set of matched skill label strings
    Failure: empty text → empty set
    """
    if text == "":
        return set()
    sBTModel = _get_model()
    userTextVec = sBTModel.encode([text])
    SkillLabels, skillVectors = _get_skill_vectors()
    scores = cosine_similarity(userTextVec, skillVectors).flatten()
    matched_indices = np.where(scores > SIMILARITY_THRESHOLD)[0]
    matched_skills = {SkillLabels[i] for i in matched_indices}
    return matched_skills
    