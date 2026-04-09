# core_engine/comparison.py

"""
Single CV↔JD comparison — the atomic unit of CareerVision.

Both Tool A and Tool B call this function.
Tool A calls it in a loop over many jobs.
Tool B calls it once for a single job.

Note: The function caller must build the skill index, and then import it here as a parameter. 
      This avoids rebuilding the skill index for every single job comparison, which is expensive. 
      The skill index is built once in the service layer and then passed down to the comparison function.
"""

from core_engine.preprocess import normalise_text
from core_engine.retrieval import _tfidf_similarity
from core_engine.skill_extraction import build_U_T, skill_gap_summary
from core_engine.scoring import aggregate
from core_engine.explanation import build_explanation


def compare_cv_to_jd(
    cv_text: str,
    jd_text: str,
    user_level: int,
    job_level: int,
    skill_index: dict,
    job_title: str = "",
    use_semantic_T: bool = False,
) -> dict:
    """
    Compare one CV against one job description.

    Inputs:
        cv_text:      raw CV string
        jd_text:      raw job description string
        user_level:   experience level 0-4 (from user)
        job_level:    seniority level 0-4 (from job model or default)
        skill_index:  pre-built skill index (pass in to avoid rebuilding per job)

    Outputs:
        result dict containing fit_score, contrib, matched,
        missing, surplus, overlap_score, explanation

    Failure case:
        Empty cv_text or jd_text → scores will be ~0 but won't crash.
    """
    # Step 1: TF-IDF similarity
    tfidf_raw = _tfidf_similarity(
        normalise_text(cv_text),
        normalise_text(jd_text)
    )

    # Step 2: skill sets
    U, T = build_U_T(cv_text, jd_text, skill_index, use_semantic_T)
    summary = skill_gap_summary(U, T)

    matched = set(summary["matched"])
    missing = set(summary["missing"])

    # Step 3: CareerFit score
    scored = aggregate(
        tfidf_raw  = tfidf_raw,
        matched    = matched,
        missing    = missing,
        T          = T,
        user_level = user_level,
        job_level  = job_level,
    )

    # Step 4: explanation
    explanation = build_explanation(
        job_title  = job_title, 
        fit_score  = scored["fit_score"],
        contrib    = scored["contrib"],
        matched    = summary["matched"],
        missing    = summary["missing"],
    )

    return {
        "fit_score":     scored["fit_score"],
        "contrib":       scored["contrib"],
        "matched":       summary["matched"],
        "missing":       summary["missing"],
        "surplus":       summary["surplus"],
        "overlap_score": summary["overlap_score"],
        "explanation":   explanation,
    }