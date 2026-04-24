# src/core_engine/explanation.py
"""
Explanation generator for CareerFit results.

Rules:
- Every sentence maps back to a computed value (score, set operation, or contrib).
- No free-form AI generation - deterministic templates only.
- This keeps explanations reproducible and defensible in evaluation.
"""

# ------------------------------------------------------------------
# Next-action templates
# Expand this dict as your corpus grows.
# Key: normalised skill label (lowercase)
# Value: concrete action the user can take
# ------------------------------------------------------------------
NEXT_ACTIONS = {
    "python":             "Add a Python project to GitHub with a README and tests.",
    "django":             "Build a small Django app (even a blog) and deploy it.",
    "sql":                "Write and commit 10 SQL queries covering JOINs, GROUP BY, and subqueries.",
    "postgresql":         "Use PostgreSQL in a project - write 5 JOIN queries against real data.",
    "git":                "Practise Git branching: create a feature branch, commit, and open a PR.",
    "docker":             "Containerise an existing project - write a Dockerfile and docker-compose.yml.",
    "rest api":           "Build a REST API with Django REST Framework - at least 3 endpoints.",
    "javascript":         "Complete a small JS project (e.g. a to-do list) without a framework.",
    "react":              "Build a React component that fetches and displays data from an API.",
    "machine learning":   "Complete one end-to-end ML project: data → model → evaluation → report.",
    "data modelling":     "Design a star schema and write 5 reporting queries against it.",
    "etl":                "Build a small ETL script: extract from CSV, transform, load into a DB.",
    "apache airflow":     "Build 1 Airflow DAG that runs a small ETL job and logs success/failure.",
    "linux":              "Set up a Linux VM and practise: file permissions, cron jobs, bash scripts.",
    "aws":                "Deploy a small app to AWS (EC2 or Lambda) and document the steps.",
}

GENERIC_ACTION = "Build evidence for '{skill}': learn the basics and add a small project example to your portfolio."


def _next_action(skill: str) -> str:
    """Return a concrete next action for a missing skill."""
    return NEXT_ACTIONS.get(skill.lower(), GENERIC_ACTION.format(skill=skill))


def _top_contributors(contrib: dict, n: int = 3) -> list[tuple[str, float]]:
    """
    Return the top-n features by weighted contribution, highest first.
    Filters out features that contributed 0.
    """
    positive = [(k, v) for k, v in contrib.items() if v > 0]
    positive.sort(key=lambda x: x[1], reverse=True)
    return positive[:n]


def _priority_missing(missing: list[str], n: int = 2, role_family: str = "") -> list[str]:
    from core_engine.market_relevance import compute_skill_frequencies
    frequencies = compute_skill_frequencies(role_family=role_family)
    result = sorted(missing, key=lambda s: frequencies.get(s, 0.0), reverse=True)[:n]
    return result

def build_explanation(
    job_title:   str,
    fit_score:   float,
    contrib:     dict,
    matched:     list[str],
    missing:     list[str],
    role_family: str = "",
) -> dict:
    """
    Build a human-readable explanation from computed values.

    Inputs:
        job_title:  display name of the job
        fit_score:  final CareerFit score (0..1)
        contrib:    per-feature weighted contributions dict
        matched:    list of matched skill labels
        missing:    list of missing skill labels

    Outputs:
        {
            "summary":        one-line match summary string,
            "top_reasons":    list of (feature, contribution) tuples,
            "matched_skills": up to 5 matched skills to display,
            "top_missing":    up to 2 most important missing skills,
            "next_actions":   list of concrete action strings,
            "fit_percent":    fit_score as a rounded percentage,
        }

    Failure case:
        If matched and missing are both empty (skill index failure),
        explanation still returns - summary will reflect low score.
        Never raises - always returns a complete dict.
    """
    fit_percent  = round(fit_score * 100, 1)
    top_reasons  = _top_contributors(contrib, n=3)
    top_missing  = _priority_missing(missing, n=2, role_family=role_family)
    next_actions = [_next_action(s) for s in top_missing]

    # Build summary sentence
    if fit_percent >= 75:
        strength = "strong"
    elif fit_percent >= 50:
        strength = "moderate"
    else:
        strength = "weak"

    summary = (
        f"You are a {strength} match for {job_title} ({fit_percent}%). "
    )

    if matched:
        summary += f"Your {', '.join(matched[:3])} skills are directly relevant."
    else:
        summary += "No direct skill matches were found."

    return {
        "summary":        summary,
        "top_reasons":    top_reasons,
        "matched_skills": matched[:5],
        "top_missing":    top_missing,
        "next_actions":   next_actions,
        "fit_percent":    fit_percent,
        "job_title":      job_title,
    }