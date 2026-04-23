# src/core_engine/scoring.py

"""
CareerFit scoring model.

Each feature returns a float in [0, 1].
Final fit_score is a weighted sum, clamped to [0, 1].

Important design choice (April 2026):
- We use embeddings ONLY as a document-level semantic similarity signal.
- We do NOT use embeddings to extract skills, because that produced untrustworthy matches.

Interpretation:
- tfidf: lexical overlap (transparent baseline)
- semantic: meaning overlap (handles synonyms)
- overlap/gap: structured skill reasoning (explainable)
- seniority: realism constraint (don’t recommend roles too far above)

Weights are tunable. Changing weights should be backed by evaluation (ablation).
"""

# ------------------------------------------------------------------
# Weights — must sum to 1.0
# Start with defendable defaults; tune later with small eval set.
# ------------------------------------------------------------------
from core_engine.market_relevance import compute_skill_frequencies

WEIGHTS = {
    "tfidf":     0.10,
    "semantic":  0.40,
    "overlap":   0.25,
    "gap":       0.10,
    "market_relevance": 0.10,
    "seniority": 0.05,
}

def _clamp(value: float) -> float:
    """Clamp a float to [0, 1]."""
    return max(0.0, min(1.0, value))


def score_tfidf(tfidf_raw: float) -> float:
    """TF-IDF cosine similarity already in [0, 1] from retrieval step."""
    return _clamp(tfidf_raw)


def score_semantic(semantic_raw: float) -> float:
    """Semantic similarity already mapped to [0, 1] by semantic_similarity()."""
    return _clamp(semantic_raw)

def score_market_relevance(missing: list[str], role_family: str) -> float:
    """
    Average market relevance of missing skills, inverted.
    0.0 = missing very high-frequency skills (bad)
    1.0 = missing only rare skills (good)
    """
    if not missing:
        return 1.0
    frequencies = compute_skill_frequencies(role_family=role_family)
    missing_freqs = [frequencies.get(s, 0.0) for s in missing]
    avg_missing_freq = sum(missing_freqs) / len(missing_freqs)
    return 1.0 - avg_missing_freq

def score_seniority(user_level: int, job_level: int) -> float:
    """
    Closeness of experience level match.
    Both values are integers on a 0..4 scale:
        0 = Intern, 1 = Graduate, 2 = Mid, 3 = Senior, 4 = Lead

    Distance of 0 → 1.0 (perfect match)
    Distance of 1 → 0.75
    Distance of 2 → 0.50
    Distance of 3 → 0.25
    Distance of 4 → 0.0

    Failure case: levels outside 0..4 are clamped before comparison.
    """
    user_level = max(0, min(4, int(user_level)))
    job_level = max(0, min(4, int(job_level)))
    distance = abs(user_level - job_level)
    return _clamp(1.0 - (distance / 4.0))


def aggregate(
    tfidf_raw: float,
    semantic_raw: float,
    overlap_score: float,
    gap_score: float,
    user_level: int,
    job_level: int,
    missing:     list[str],
    role_family: str = "",
) -> dict:
    """
    Compute all features, apply weights, return fit_score + breakdown. overlap and score gap are computed in skill_extraction.py and passed in here for aggregation.

    Inputs:
        tfidf_raw:  raw cosine similarity from retrieval step
        semantic_raw: raw semantic similarity from sentence-transformers
        overlap_score:  score for overlapping skills
        gap_score:  score for skill gaps
        market_relevance: score for market relevance of missing skills
        user_level: user's experience level (0–4)
        job_level:  job's seniority level (0–4)


    Outputs:
        {
            "fit_score":  float (0..1),  # final weighted score
            "contrib": {                 # per-feature breakdown
                "tfidf":     float,
                "semantic":  float,
                "overlap":   float,
                "gap":       float,
                "seniority": float,
                "market_relevance": float,
            }
        }

    Failure case:
        All inputs default gracefully — empty sets return 0.0 scores,
        not exceptions.
    """
    scores = {
        "tfidf": score_tfidf(tfidf_raw),
        "semantic": score_semantic(semantic_raw),
        "overlap": overlap_score,
        "gap": gap_score,
        "seniority": score_seniority(user_level, job_level),
        "market_relevance": score_market_relevance(missing=missing, role_family=role_family),  # Placeholder, will be updated in comparison.py after missing skills are known

    }

    fit_score = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    contrib = {k: round(WEIGHTS[k] * scores[k], 4) for k in WEIGHTS}

    return {
        "fit_score": round(_clamp(fit_score), 4),
        "contrib": contrib,
    }
