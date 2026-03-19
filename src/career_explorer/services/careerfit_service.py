# src/career_explorer/services/careerfit_service.py

from career_explorer.models import Job
from core_engine.preprocess import normalise_text
from core_engine.retrieval import retrieve_top_m
from core_engine.skill_extraction import _build_skill_index, build_U_T, skill_gap_summary
from core_engine.scoring import aggregate
from core_engine.explanation import build_explanation


def run_careerfit(cv_text: str, user_level: int = 1, M: int = 10) -> list[dict]:
    """
    Full CareerFit pipeline for one CV against the job corpus.

    Inputs:
        cv_text:    raw CV string
        user_level: experience level 0–4 (default 1 = Graduate)
        M:          max results to return

    Outputs:
        List of result dicts, ordered by fit_score descending.
        Each dict contains: job, fit_score, contrib, matched, missing, surplus, overlap_score

    Failure case:
        Empty corpus → returns [].
        Empty CV text → all scores will be ~0 but won't crash.
    """
    jobs = list(Job.objects.all())
    if not jobs:
        return []

    # Step 1: TF-IDF shortlist
    job_texts  = [normalise_text(j.description) for j in jobs]
    cv_clean   = normalise_text(cv_text)
    top_m      = retrieve_top_m(cv_clean, job_texts, M=min(M, len(jobs)))

    # Step 2: Build skill index once (expensive — one DB call)
    skill_index = _build_skill_index()

    results = []

    for idx, tfidf_raw in top_m:
        job = jobs[idx]

        # Step 3: Extract U and T
        U, T = build_U_T(cv_text, job.description, skill_index)
        summary = skill_gap_summary(U, T)

        matched = set(summary["matched"])
        missing = set(summary["missing"])

        # Step 4: CareerFit score
        scored = aggregate(
            tfidf_raw  = tfidf_raw,
            matched    = matched,
            missing    = missing,
            T          = T,
            user_level = user_level,
            job_level  = job.seniority_level,
        )

        explanation = build_explanation(
            job_title=job.title,
            fit_score=scored["fit_score"],
            contrib=scored["contrib"],
            matched=summary["matched"],
            missing=summary["missing"],
        )

        results.append({
            "job": job,
            "fit_score": scored["fit_score"],
            "contrib": scored["contrib"],
            "matched": summary["matched"],
            "missing": summary["missing"],
            "surplus": summary["surplus"],
            "overlap_score": summary["overlap_score"],
            "explanation": explanation,
        })

    # Sort by fit_score, best first
    results.sort(key=lambda r: r["fit_score"], reverse=True)
    return results