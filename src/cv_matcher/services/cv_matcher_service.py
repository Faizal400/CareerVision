# cv_matcher/services/cv_matcher_service.py

from core_engine.skill_extraction import _build_skill_index
from core_engine.comparison import compare_cv_to_jd


def run_cvmatcher(cv_text: str, jd_text: str, user_level: int = 1) -> dict:
    """
    Tool B: compare one CV against one JD directly.

    Inputs:
        cv_text:    raw CV string
        jd_text:    raw job description string
        user_level: experience level 0-4

    Outputs:
        Single result dict with fit_score, explanation,
        matched/missing/surplus skills.
    """
    skill_index = _build_skill_index()
    jd_title = jd_text.strip().split("\n")[0][:80] or "Target Role"
    result = compare_cv_to_jd(
        cv_text     = cv_text,
        jd_text     = jd_text,
        user_level  = user_level,
        job_level   = 1,
        skill_index = skill_index,
        job_title   = jd_title,
    )

    return result