# career_explorer/services/careerexplorer_service.py

from career_explorer.models import Job
from core_engine.preprocess import normalise_text
from core_engine.retrieval import retrieve_top_m
from core_engine.comparison import compare_cv_to_jd


def run_careerexplorer(cv_text: str, 
                       user_level: int = 1, 
                       M: int = 10) -> list[dict]:
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

    # Step 1: TF-IDF shortlist - efficient retrieval
    job_texts = [normalise_text(j.description) for j in jobs]
    cv_clean  = normalise_text(cv_text)
    t0 = time.time()
    top_m     = retrieve_top_m(cv_clean, job_texts, M=min(M, len(jobs)))

    results = []

    # Step 2: CareerFit score for each shortlisted job
    t0 = time.time()
    for idx, _ in top_m:
        job = jobs[idx]

        result = compare_cv_to_jd(
            cv_text    = cv_text,
            jd_text    = job.description,
            user_level = user_level,
            job_level  = job.seniority_level,
            job_title= job.title,
            ESCOoccupation=job.esco_occupation,
            role_family=job.role_family
        ) 
        # compare_cv_to_jd calls extract_skills(). extract_skills() calls _build_phrases_rules which checks cache first.
        # So we aren't rebuilding the phrase rules for every job, just once on the first call. Subsequent calls are faster

        # Attach job metadata and fix job title in explanation
        result["job"] = job

        results.append(result)

    results.sort(key=lambda r: r["fit_score"], reverse=True)
    return results