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

# Human-friendly labels for debug UI / explanation
FEATURE_LABELS = {
    "semantic": "Semantic similarity (meaning)",
    "tfidf": "Keyword similarity (TF-IDF)",
    "overlap": "Skill overlap (what you already have)",
    "gap": "Skill coverage (few gaps = good)",
    "market_relevance": "Market relevance (importance)",
    "seniority": "Seniority realism",
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

# --- CareerFit aggregate ---

def aggregate(
    tfidf_raw: float,
    semantic_raw: float,
    overlap_score: float,
    gap_score: float,
    user_level: int,
    job_level: int,
    missing: list[str],
    role_family: str = "",
) -> dict:
    """
    Compute all features, apply weights, return fit_score + breakdown + debug.

    IMPORTANT:
    - All feature scores are in [0, 1] where 1 is "good".
    - contrib = weight * feature, so the maximum contribution is the weight.
    - In this project, "gap_score" is implemented as a GOODNESS score:
        1.0 = few/no gaps (good)
        0.0 = many gaps (bad)
      (So gap is not subtracted; it is a positive “coverage” contribution.)
    """

    # 1) Raw feature values (normalised to 0..1)
    scores = {
        "tfidf": score_tfidf(tfidf_raw),
        "semantic": score_semantic(semantic_raw),
        "overlap": _clamp(overlap_score),
        "gap": _clamp(gap_score),  # GOODNESS score (1 = low gaps)
        "market_relevance": _clamp(score_market_relevance(missing=missing, role_family=role_family)),
        "seniority": score_seniority(user_level, job_level),
    }

    # 2) Weighted contributions (each capped by its weight)
    contrib = {k: round(float(WEIGHTS[k]) * float(scores[k]), 4) for k in WEIGHTS}

    # 3) Final score = sum of weighted contributions (then clamped)
    fit_score = _clamp(sum(contrib.values()))
    fit_score = round(fit_score, 4)

    # 4) Full debug breakdown + display-ready story rows
    debug = {
        "raw": {k: round(float(scores[k]), 4) for k in WEIGHTS},     # 0..1 per feature
        "weights": {k: float(WEIGHTS[k]) for k in WEIGHTS},          # caps
        "contrib": contrib,                                          # weight * raw
        "final": fit_score,
        "inputs": {
            "tfidf_raw": round(float(tfidf_raw), 4),
            "semantic_raw": round(float(semantic_raw), 4),
            "user_level": int(user_level),
            "job_level": int(job_level),
            "missing_count": int(len(missing)),
            "role_family": (role_family or "").strip(),
        },
        "note": {
            "gap": "gap is implemented as a COVERAGE/GOODNESS score (1 = few gaps). It contributes positively.",
            "max_contrib_rule": "Max contribution per feature = its weight, because raw scores are clamped to 0..1.",
        },
    }

    # Build coherent, display-ready table rows
    rows = []
    for k in WEIGHTS:
        raw = float(scores[k])
        w = float(WEIGHTS[k])
        c = float(contrib[k])
        rows.append({
            "key": k,
            "label": FEATURE_LABELS.get(k, k),
            "raw": round(raw, 4),                         # 0..1
            "raw_pct": int(round(raw * 100)),             # 0..100 (use for bars)
            "weight": round(w, 4),                        # cap
            "contrib": round(c, 4),                       # weight * raw
            "cap_note": f"max {w:.2f}",
        })

    # Sort by contribution (largest drivers first)
    rows.sort(key=lambda r: r["contrib"], reverse=True)

    # Top drivers (first 3 biggest contributions)
    drivers = [
        f"{r['label']} ({r['contrib']:.2f}/{r['weight']:.2f})"
        for r in rows[:3]
    ]

    debug["rows"] = rows
    debug["drivers"] = drivers
    debug["story"] = {
        "headline": f"Final score = {fit_score:.3f} (sum of weighted feature contributions).",
        "drivers": drivers,
        "rule": "Each feature contributes weight × raw_score. Raw scores are 0–1, so a feature can never contribute more than its weight.",
    }

    return {
        "fit_score": fit_score,
        "contrib": contrib, 
        "debug": debug, # full breakdown + rows/story for UI
    }