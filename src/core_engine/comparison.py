# core_engine/comparison.py

"""
Single CV↔JD comparison — the atomic unit of CareerVision.

Both Tool A and Tool B call this function.
Tool A calls it in a loop over many jobs.
Tool B calls it once for a single job.

Design principle:
- The comparison function is deterministic and testable.
- The calling layer is responsible for UI and persistence.
"""

from core_engine.preprocess import normalise_text
from core_engine.retrieval import _tfidf_similarity
from core_engine.skill_extraction import build_U_T, skill_gap_summary
from core_engine.semantic_similarity import semantic_similarity
from core_engine.scoring import aggregate
from core_engine.explanation import build_explanation


def compare_cv_to_jd(
    cv_text: str,
    jd_text: str,
    user_level: int,
    job_level: int,
    job_title: str = "",
    ESCOoccupation=None
) -> dict:
    """
    Compare one CV against one job description.

    Inputs:
        cv_text:      raw CV string
        jd_text:      raw job description string
        user_level:   experience level 0-4 (from user)
        job_level:    seniority level 0-4 (from job model or user input)

    Outputs:
        dict containing:
          - fit_score
          - contrib (weighted feature contributions)
          - matched/missing/surplus skills
          - overlap_score
          - explanation (summary + next actions)
          - raw feature scores (tfidf_raw, semantic_raw)

    Failure case:
        Empty cv_text or jd_text → scores ~0 but won't crash.
    """
    cv_norm = normalise_text(cv_text)
    jd_norm = normalise_text(jd_text)

    # 1) Baseline lexical similarity (transparent)
    tfidf_raw = _tfidf_similarity(cv_norm, jd_norm)

    # 2) Semantic similarity (meaning)
    # We compute on normalised text for stability.
    semantic_raw = semantic_similarity(cv_norm, jd_norm)

    # 3) Skill sets (precision-first)
    U, T_ess, T_opt = build_U_T(cv_text, jd_text, occupation=ESCOoccupation)
    summary = skill_gap_summary(U, T_ess, T_opt)

    matched = set(summary["matched"])
    missing = set(summary["missing"])

    # 4) Aggregate CareerFit score
    scored = aggregate(
        tfidf_raw=tfidf_raw,
        semantic_raw=semantic_raw,
        overlap_score=summary["overlap_score"],
        gap_score=summary["gap_score"],
        user_level=user_level,
        job_level=job_level,
    )

    # 5) Explanation (deterministic templates)
    explanation = build_explanation(
        job_title=job_title,
        fit_score=scored["fit_score"],
        contrib=scored["contrib"],
        matched=summary["matched"],
        missing=summary["missing"],
    )

    return {
        "fit_score": scored["fit_score"],
        "contrib": scored["contrib"],
        "matched": summary["matched"],
        "missing": summary["missing"],
        "surplus": summary["surplus"],
        "overlap_score": summary["overlap_score"],
        "explanation": explanation,
        "tfidf_raw": round(tfidf_raw, 4),
        "semantic_raw": round(semantic_raw, 4),
    }
