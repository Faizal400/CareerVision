# cv_matcher/services/cv_matcher_service.py

from core_engine.comparison import compare_cv_to_jd


def infer_job_level_from_text(jd_text: str) -> int:
    """
    Lightweight heuristic seniority inference for pasted JDs (Tool B).
    Returns 0..4 scale:
      0=Intern, 1=Graduate/Junior, 2=Mid, 3=Senior, 4=Lead/Principal
    """
    t = (jd_text or "").lower()
    if any(k in t for k in ["intern", "placement", "apprentice"]):
        return 0
    if any(k in t for k in ["graduate", "junior", "entry level", "entry-level"]):
        return 1
    if any(k in t for k in ["senior"]):
        return 3
    if any(k in t for k in ["lead", "principal", "staff", "head of"]):
        return 4
    # default: assume mid if unclear
    return 2


def run_cvmatcher(cv_text: str, 
                  jd_text: str, 
                  user_level: int = 1, 
                  job_level: int | None = None, 
                  job_title: str | None = None) -> dict:
    """
    Tool B: compare one CV against one JD directly.

    Inputs:
        cv_text:    raw CV string
        jd_text:    raw job description string
        user_level: experience level 0-4
        job_level:  optional override (0-4). If None, inferred.
        job_title:  optional override. If None, uses a safe default.

    Outputs:
        Single result dict with fit_score, explanation,
        matched/missing/surplus skills.
    """
    if job_title is None or not job_title.strip():
        job_title = "Pasted Job Description"
    if job_level is None:
        job_level = infer_job_level_from_text(jd_text)

    result = compare_cv_to_jd(
        cv_text=cv_text,
        jd_text=jd_text,
        user_level=user_level,
        job_level=job_level,
        job_title=job_title,
    )
    return result
