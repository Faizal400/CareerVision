# src/career_explorer/services/retrieval_service.py

from career_explorer.models import Job
from core_engine.preprocess import normalise_text
from core_engine.retrieval import retrieve_top_m


def get_top_jobs(cv_text: str, M: int = 10) -> list[tuple[Job, float]]:
    """
    Given raw CV text, return the top-M matching Jobs with their TF-IDF scores.

    Inputs:
        cv_text: raw string from CV upload or paste
        M:       how many results to return (default 10)

    Outputs:
        list of (Job, score) tuples, ordered best-first

    Failure case:
        If no jobs exist in the DB, returns an empty list.
        If cv_text is empty after normalisation, scores will all be ~0.
    """
    jobs = list(Job.objects.all())

    if not jobs:
        return []

    job_texts = [normalise_text(j.description) for j in jobs]
    cv_clean  = normalise_text(cv_text)

    top = retrieve_top_m(cv_clean, job_texts, M=min(M, len(jobs)))

    return [(jobs[idx], score) for idx, score in top]