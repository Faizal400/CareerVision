# src/core_engine/skill_extraction.py
import re
from core_engine.preprocess import normalise_text

# Skills with labels shorter than this are too risky for substring matching
MIN_LABEL_LENGTH = 3

# Manual aliases: what appears in real CVs → canonical skill label
# Expand this list as you spot misses in testing
SKILL_ALIASES = {
    "python":        "Python",
    "django":        "Django",
    "sql":           "SQL",
    "git":           "Git",
    "docker":        "Docker",
    "linux":         "Linux",
    "rest api":      "REST API",
    "rest apis":     "REST API",
    "postgresql":    "PostgreSQL",
    "postgres":      "PostgreSQL",
    "airflow":       "Apache Airflow",
    "scikit-learn":  "scikit-learn",
    "pandas":        "pandas",
    "numpy":         "NumPy",
    "javascript":    "JavaScript",
    "typescript":    "TypeScript",
    "react":         "React",
    "node.js":       "Node.js",
    "nodejs":        "Node.js",
    "machine learning": "machine learning",
    "data modelling":   "data modelling",
    "data modeling":    "data modelling",
    "etl":           "ETL",
    "aws":           "AWS",
    "azure":         "Microsoft Azure",
    "gcp":           "Google Cloud",
}


def _whole_word_match(label: str, text: str) -> bool:
    """
    Returns True if `label` appears as whole words in `text`.
    Prevents 'r' matching inside 'career' or 'rest'.
    """
    pattern = r'\b' + re.escape(label) + r'\b'
    return bool(re.search(pattern, text))


def _extract_keyword(label: str) -> str:
    """
    Pull the most meaningful word from a long ESCO label.
    "use Python scripting language" → "python"
    "develop software applications" → "software"

    Strategy: take the longest word that isn't a stopword.
    """
    STOPWORDS = {
        "use", "using", "with", "and", "or", "of", "in", "to",
        "for", "the", "a", "an", "develop", "create", "manage",
        "apply", "work", "provide", "ensure", "perform", "support",
        "implement", "define", "analyse", "analyze", "design",
        "build", "write", "maintain", "review", "prepare",
    }
    words = [w for w in label.split() if w not in STOPWORDS and len(w) >= MIN_LABEL_LENGTH]
    if not words:
        return label  # fallback: keep original
    return max(words, key=len)  # pick the longest meaningful word


def _build_skill_index() -> dict[str, str]:
    """
    Builds two-layer skill index:
    Layer 1: aliases from SKILL_ALIASES (highest precision)
    Layer 2: keywords extracted from ESCO labels (broader coverage)

    Keys:   normalised match string
    Values: display label shown to user
    """
    from career_explorer.models import ESCOSkill

    index = {}

    # Layer 1: manual aliases always win
    for alias, canonical in SKILL_ALIASES.items():
        index[normalise_text(alias)] = canonical

    # Layer 2: ESCO labels — extract keyword, skip if too short
    for skill in ESCOSkill.objects.all():
        normalised_label = normalise_text(skill.skill_label)

        # Skip if too short — too risky for whole-word matching
        if len(normalised_label) < MIN_LABEL_LENGTH:
            continue

        keyword = _extract_keyword(normalised_label)

        # Don't overwrite an alias with a weaker ESCO match
        if keyword not in index:
            index[keyword] = skill.skill_label

    return index


def extract_skills(text: str, skill_index: dict[str, str]) -> set[str]:
    """
    Given text and a skill index, return matched skill labels.
    Uses whole-word matching to prevent false positives.
    """
    if not text:
        return set()

    normalised = normalise_text(text)
    matched = set()

    for keyword, label in skill_index.items():
        if _whole_word_match(keyword, normalised):
            matched.add(label)

    return matched


def build_U_T(cv_text: str, job_description: str,
              skill_index: dict[str, str]) -> tuple[set[str], set[str]]:
    """
    Build user skill set U and target skill set T.
    """
    U = extract_skills(cv_text, skill_index)
    T = extract_skills(job_description, skill_index)
    return U, T


def skill_gap_summary(U: set[str], T: set[str]) -> dict:
    """
    Returns matched, missing, surplus skills and overlap score.
    """
    matched = U & T
    missing = T - U
    surplus = U - T

    overlap_score = len(matched) / len(T) if T else 0.0

    return {
        "matched":       sorted(matched),
        "missing":       sorted(missing),
        "surplus":       sorted(surplus),
        "overlap_score": round(overlap_score, 4),
    }