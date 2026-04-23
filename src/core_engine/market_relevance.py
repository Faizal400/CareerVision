from django.core.cache import cache
from career_explorer.models import Job
from core_engine.skill_extraction import extract_skills
from core_engine.preprocess import normalise_text

def compute_skill_frequencies(role_family=None) -> dict[str, float]:
    """
    Returns a dict mapping skill label -> frequency (0..1)
    across all jobs in the corpus.
    Cached after first computation.
    """
    cache_key = f"skill_frequencies::{(role_family or 'all').strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    jobs = list(Job.objects.filter(role_family=role_family) if role_family else Job.objects.all())
    if not jobs:
        return {}
    
    skill_counts: dict[str, int] = {}
    for job in jobs:
        skills = extract_skills(job.description)
        for skill in skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    total_jobs = len(jobs)
    frequencies = {skill: count / total_jobs 
                   for skill, count in skill_counts.items()}
    
    cache.set("skill_frequencies", frequencies, timeout=None)
    return frequencies


def get_skill_market_relevance(skill: str) -> float:
    """Return market relevance score (0..1) for a single skill."""
    frequencies = compute_skill_frequencies()
    return frequencies.get(skill, 0.0)

# ||| Role family classifier: --------------------------------------------
TECH_SOFTWARE_KEYWORDS = {
    "software", "developer", "development", "programmer", "programming",
    "frontend", "backend", "fullstack", "full stack", "full-stack",
    "web", "mobile", "ios", "android", "application", "api",
    "game", "embedded", "firmware", "blockchain", "solidity",
    "scrum", "agile", "product manager", "product management",
    "technical writer", "qa", "tester", "testing", "quality assurance",
    "ux", "ui", "user experience", "user interface", "designer"
}

TECH_DATA_KEYWORDS = {
    "data", "analyst", "analytics", "scientist", "science",
    "machine learning", "ml", "ai", "artificial intelligence",
    "nlp", "natural language", "computer vision", "deep learning",
    "business intelligence", "bi", "etl", "pipeline", "warehouse",
    "databricks", "snowflake", "spark", "hadoop", "kafka",
    "bioinformatics", "quantitative", "research engineer"
}

TECH_INFRA_KEYWORDS = {
    "devops", "cloud", "infrastructure", "platform", "sre",
    "reliability", "kubernetes", "docker", "terraform", "ansible",
    "network", "networking", "security", "cyber", "penetration",
    "systems", "automation", "robotics", "iot", "embedded systems",
    "gis", "database administrator", "dba"
}

NON_TECH_KEYWORDS = {
    "marketing", "hr", "human resources", "recruiter", "recruitment",
    "finance", "financial", "accounting", "accountant", "audit",
    "legal", "paralegal", "lawyer", "solicitor", "compliance",
    "journalist", "journalism", "writer", "editor", "media",
    "teacher", "teaching", "education", "lecturer", "tutor",
    "nurse", "nursing", "healthcare", "clinical", "medical",
    "social worker", "counsellor", "therapist", "psychologist",
    "architect", "urban planner", "surveyor", "civil engineer",
    "environmental", "supply chain", "logistics", "procurement",
    "pr", "public relations", "communications", "policy"
}
def _classify_from_text(text: str) -> str:
    if any(k in text for k in TECH_DATA_KEYWORDS):
        return "tech_data"
    elif any(k in text for k in TECH_SOFTWARE_KEYWORDS):
        return "tech_software"
    elif any(k in text for k in TECH_INFRA_KEYWORDS):
        return "tech_infrastructure"
    elif any(k in text for k in NON_TECH_KEYWORDS):
        return "non_tech"
    return "other"