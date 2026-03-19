# src/core_engine/scoring.py

"""
CareerFit scoring model.

Each feature returns a float in [0, 1].
Final fit_score is a weighted sum, clamped to [0, 1].

Weights are documented and tunable — see WEIGHTS dict.
Changing a weight requires updating the decision log.
"""

# ------------------------------------------------------------------
# Weights — must sum to 1.0
# Documented rationale in decision log (P7)
# ------------------------------------------------------------------
WEIGHTS = {
    "tfidf":    0.30,   # broad text similarity
    "overlap":  0.40,   # skill match — highest weight, most direct signal
    "gap":      0.20,   # penalise large missing skill counts
    "seniority": 0.10,  # experience level alignment
}


def _clamp(value: float) -> float:
    """Clamp a float to [0, 1]."""
    return max(0.0, min(1.0, value))


def score_tfidf(tfidf_raw: float) -> float:
    """
    Pass-through for TF-IDF cosine similarity.
    Already in [0, 1] from retrieval step.
    """
    return _clamp(tfidf_raw)


def score_overlap(matched: set, T: set) -> float:
    """
    Fraction of required skills (T) that the user has.
    0.0 = none of the required skills matched.
    1.0 = all required skills matched.

    Failure case: if T is empty, returns 0.0 (no division by zero).
    """
    if not T:
        return 0.0
    return _clamp(len(matched) / len(T))


def score_gap(missing: set, T: set) -> float:
    """
    Inverted gap score — penalises missing skills.
    0.0 = missing everything.
    1.0 = missing nothing.

    Formula: 1 - (|missing| / |T|)
    Failure case: if T is empty, returns 1.0 (no penalty).
    """
    if not T:
        return 1.0
    gap_ratio = len(missing) / len(T)
    return _clamp(1.0 - gap_ratio)


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
    user_level = max(0, min(4, user_level))
    job_level  = max(0, min(4, job_level))
    distance   = abs(user_level - job_level)
    return _clamp(1.0 - (distance / 4.0))


def aggregate(
    tfidf_raw:   float,
    matched:     set,
    missing:     set,
    T:           set,
    user_level:  int,
    job_level:   int,
) -> dict:
    """
    Compute all features, apply weights, return fit_score + breakdown.

    Inputs:
        tfidf_raw:  raw cosine similarity from retrieval step
        matched:    U ∩ T  (skills user has that job requires)
        missing:    T − U  (skills job requires that user lacks)
        T:          full target skill set from job
        user_level: user's experience level (0–4)
        job_level:  job's seniority level (0–4)

    Outputs:
        {
            "fit_score":  float (0..1),  # final weighted score
            "contrib": {                 # per-feature breakdown
                "tfidf":     float,
                "overlap":   float,
                "gap":       float,
                "seniority": float,
            }
        }

    Failure case:
        All inputs default gracefully — empty sets return 0.0 scores,
        not exceptions.
    """
    scores = {
        "tfidf":     score_tfidf(tfidf_raw),
        "overlap":   score_overlap(matched, T),
        "gap":       score_gap(missing, T),
        "seniority": score_seniority(user_level, job_level),
    }

    fit_score = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)

    # contrib shows weighted contribution of each feature
    contrib = {k: round(WEIGHTS[k] * scores[k], 4) for k in WEIGHTS}

    return {
        "fit_score": round(_clamp(fit_score), 4),
        "contrib":   contrib,
    }