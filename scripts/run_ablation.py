"""Run a simple ablation study over the current job corpus.

This script is *not* part of the web app runtime.
It exists as build-phase evidence that the scoring model is justified.

It computes four score variants per job:
1) tfidf_only
2) skill_only (overlap + gap)
3) semantic_only
4) full_careerfit (the app's fit_score)

Usage (from repo root):
  python scripts/run_ablation.py

If sentence-transformers is not installed, semantic scores will be 0.0.
"""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
sys.path.insert(0, str(SRC))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from career_explorer.models import Job
from core_engine.comparison import compare_cv_to_jd


# ---------------------------
# Config: choose a CV sample
# ---------------------------
SAMPLE_CV = """
Third-year Computer Science student. Interested in backend/web development.
Python, Django, SQL, Git/GitHub, Docker, Linux basics. REST APIs.
""".strip()


def main() -> None:
    jobs = list(Job.objects.all())
    if not jobs:
        print("No jobs in DB. Run: cd src && python manage.py load_jobs")
        return

    rows = []
    for job in jobs:
        r = compare_cv_to_jd(
            cv_text=SAMPLE_CV,
            jd_text=job.description,
            user_level=1,
            job_level=job.seniority_level,
            job_title=job.title,
            ESCOoccupation=job.esco_occupation,
            role_family=job.role_family,
        )

        tfidf = float(r.get("tfidf_raw", 0.0))
        semantic = float(r.get("semantic_raw", 0.0))
        overlap = float(r.get("overlap_score", 0.0))
        # gap_score in this codebase is already "goodness" (1 means no gap)
        gap_good = float(r.get("contrib", {}).get("gap", 0.0))

        # A simple, explainable skill-only score for ablation evidence.
        skill_only = 0.6 * overlap + 0.4 * (1.0 if not r.get("missing") else 0.6)

        rows.append(
            {
                "title": job.title,
                "tfidf_only": tfidf,
                "semantic_only": semantic,
                "skill_only": round(skill_only, 4),
                "full_careerfit": r["fit_score"],
            }
        )

    def show(name: str, key: str) -> None:
        print("\n==", name, "==")
        top = sorted(rows, key=lambda x: x[key], reverse=True)[:10]
        for i, row in enumerate(top, 1):
            print(f"{i:>2}. {row['title'][:50]:50}  {key}={row[key]:.4f}")

    show("TF-IDF only", "tfidf_only")
    show("Skill features only", "skill_only")
    show("Semantic only", "semantic_only")
    show("Full CareerFit", "full_careerfit")


if __name__ == "__main__":
    main()
