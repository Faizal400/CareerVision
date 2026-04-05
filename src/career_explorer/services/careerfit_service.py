# career_explorer/services/careerfit_service.py

from career_explorer.models import Job
from core_engine.preprocess import normalise_text
from core_engine.retrieval import retrieve_top_m
from core_engine.skill_extraction import _build_skill_index
from core_engine.comparison import compare_cv_to_jd


def run_careerfit(cv_text: str, user_level: int = 1, M: int = 10) -> list[dict]:
    """
    Tool A pipeline: retrieve top-M jobs by TF-IDF, then
    re-rank each using compare_cv_to_jd (CareerFit).

    Inputs:
        cv_text:    raw CV string
        user_level: experience level 0-4
        M:          max results to return

    Outputs:
        List of result dicts ordered by fit_score descending.
        Each dict contains job, fit_score, contrib,
        matched, missing, surplus, overlap_score, explanation.
    """
    jobs = list(Job.objects.all())
    if not jobs:
        return []

    # Step 1: TF-IDF shortlist — efficient retrieval
    job_texts = [normalise_text(j.description) for j in jobs]
    cv_clean  = normalise_text(cv_text)
    top_m     = retrieve_top_m(cv_clean, job_texts, M=min(M, len(jobs)))

    # Step 2: build skill index once — shared across all comparisons
    skill_index = _build_skill_index()

    results = []

    # Step 3: CareerFit score for each shortlisted job
    for idx, _ in top_m:
        job = jobs[idx]

        result = compare_cv_to_jd(
            cv_text    = cv_text,
            jd_text    = job.description,
            user_level = user_level,
            job_level  = job.seniority_level,
            skill_index = skill_index,
            job_title= job.title,
        )

        # Attach job metadata and fix job title in explanation
        result["job"] = job
        #result["explanation"]["job_title"] = job.title

        results.append(result)

    results.sort(key=lambda r: r["fit_score"], reverse=True)
    return results