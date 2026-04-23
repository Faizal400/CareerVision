# src/core_engine/skill_extraction.py
"""
Precision-first skill extraction.

Why this exists:
- Previous approach extracted a single "keyword" from long ESCO labels.
  Causing catastrophic false positives (e.g., "clean building facade" matched from "clean interfaces").
- For an FYP, credibility matters more than recall. A smaller, correct set beats a large, wrong set.

Design:
- Layer 1 (primary): curated aliases/synonyms for common tech skills (high precision).
- Layer 2 (optional): ESCO label phrase matching, but ONLY for labels that look "tech-like"
  and ONLY via multi-word phrase matching (no single-word keyword extraction).

Important:
- Semantic *skill extraction* is DISABLED (by design). Embeddings are used only for
  CV↔JD semantic similarity at the document level (see core_engine/semantic_similarity.py). 
  Similar to how I did tfidf-based similarity in the previous version, but more robust and with better performance and results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable
from django.core.cache import cache
from core_engine.preprocess import normalise_text
from core_engine.skill_aliases import SKILL_ALIASES, TECH_SEED_TOKENS
from career_explorer.models import OccupationSkillRelation


# Tokens that are too generic; we never treat these alone as skills.
GENERIC_TOKENS = {
    "use", "using", "work", "working", "build", "building", "design", "develop",
    "manage", "support", "provide", "ensure", "perform", "create", "apply",
    "data", "model", "models", "systems", "platform", "platforms", "tool", "tools",
    "team", "teams", "experience", "environment", "solution", "solutions",
    "reliable", "reliability", "scalable", "scalability",
}

# Tokens that indicate clearly non-tech ESCO skills that caused false positives in your tests.
# This is a defensive filter for the optional ESCO phrase layer.
BANNED_DOMAIN_TOKENS = {
    "timber", "facade", "artist", "shipping", "wire", "hand", "tools",
    "building", "commercial", "sell", "processed", "furniture", "construction",
}


# -----------------------------
# Optional ESCO phrase layer
# -----------------------------
# Only keep ESCO labels that look like technical skills.
# If you want maximum simplicity, you can set ENABLE_ESCO_PHRASES = False.
ENABLE_ESCO_PHRASES = True

STOPWORDS = {
    "and", "or", "of", "in", "to", "for", "the", "a", "an", "with", "on", "at", "by",
}


@dataclass(frozen=True)
class PhraseRule:
    """A phrase and its canonical label, plus tokens for fast matching."""
    phrase: str          # normalised phrase, e.g. "model serving"
    label: str           # display label, e.g. "Model serving"
    tokens: frozenset[str]


def _tokenise(s: str) -> list[str]:
    return [t for t in normalise_text(s).split() if t]


def _is_esco_label_tech_like(label: str) -> bool:
    tokens = _tokenise(label)

    # Reject single-word ESCO labels entirely (too risky) unless alias layer covers them.
    if len(tokens) < 2:
        return False

    # Reject if any banned domain token appears
    if any(t in BANNED_DOMAIN_TOKENS for t in tokens):
        return False

    # Need at least one tech seed token
    if not any(t in TECH_SEED_TOKENS for t in tokens):
        return False

    # Require >=2 meaningful tokens (not stopwords / generic)
    meaningful = [t for t in tokens if t not in STOPWORDS and t not in GENERIC_TOKENS and len(t) >= 3]
    return len(meaningful) >= 2


def _build_phrase_rules() -> list[PhraseRule]:
    """
    Build a cached list of PhraseRule objects:
    - aliases (always)
    - optional ESCO phrase rules (filtered to tech-like)
    """
    cached = cache.get("phrase_rules_v2")
    if cached is not None:
        return cached

    rules: list[PhraseRule] = []

    # Layer 1: curated aliases
    for alias, canonical in SKILL_ALIASES.items():
        phrase = normalise_text(alias)
        tokens = frozenset(_tokenise(phrase))
        if not tokens:
            continue
        rules.append(PhraseRule(phrase=phrase, label=canonical, tokens=tokens))

    if ENABLE_ESCO_PHRASES:
        from career_explorer.models import ESCOSkill

        for s in ESCOSkill.objects.all().only("skill_label"):
            label = s.skill_label
            if not label:
                continue
            if not _is_esco_label_tech_like(label):
                continue
            phrase = normalise_text(label)
            tokens = frozenset(_tokenise(phrase))
            if len(tokens) < 2:
                continue
            rules.append(PhraseRule(phrase=phrase, label=label, tokens=tokens))

    # De-duplicate by (phrase,label)
    dedup = {}
    for r in rules:
        dedup[(r.phrase, r.label)] = r
    rules = list(dedup.values())

    cache.set("phrase_rules_v2", rules, timeout=None)
    return rules


def extract_skills(text: str) -> set[str]:
    """
    Extract a set of skill labels from text using phrase rules.

    Matching rule:
    - For multi-word phrases: require the exact phrase substring to appear in the normalised text.
      (This avoids matching words that appear far apart.)
    - For single tokens: aliases cover them; ESCO single-token labels are not used.
    """
    if not text:
        return set()

    norm = normalise_text(text)
    matched: set[str] = set()

    rules = _build_phrase_rules()

    # Fast path: exact substring for multi-word phrases
    for r in rules:
        if len(r.tokens) >= 2:
            if r.phrase and r.phrase in norm:
                matched.add(r.label)
        else:
            # single token alias match (word boundary)
            tok = next(iter(r.tokens))
            if re.search(r"\b" + re.escape(tok) + r"\b", norm):
                matched.add(r.label)

    return matched


def build_U_T(cv_text: str, job_description: str, occupation=None) -> tuple[set[str], set[str], set[str]]:
    """
    Build:
    - U: user skills extracted from CV
    - T: target skills extracted from job description

    Note: semantic skill extraction is disabled.
    """
    U = extract_skills(cv_text)
    T = extract_skills(job_description)
    if occupation is not None:
        relations = OccupationSkillRelation.objects.filter(
            occupation=occupation
            ).select_related("skill")
        ess_canonical = set()
        opt_canonical = set()
        for r in relations:
            canonical = extract_skills(r.skill.skill_label)  # returns set
            if r.relation_type == "essential":
                ess_canonical |= canonical
            else:
                opt_canonical |= canonical
        T_classified = ess_canonical | opt_canonical
        T_unclassified = T - T_classified  # skills ESCO didn't give us a relation for
        T_ess = (T & ess_canonical) | T_unclassified  # unclassified treated as essential
        T_opt = T & opt_canonical
    else:
        T_ess = T
        T_opt = set()
    
    return U, T_ess, T_opt


WEIGHT_ESS = 2
WEIGHT_OPT = 1

def skill_gap_summary(U: set[str], T_ess: set[str], T_opt: set[str]) -> dict:
    """
    Returns matched, missing, surplus and weighted overlap/gap scores.
    When no occupation is known, pass T_opt=set() — degrades gracefully to flat scoring.
    """
    matched_ess = U & T_ess
    matched_opt = U & T_opt
    missing_ess = T_ess - U
    missing_opt = T_opt - U
    surplus     = U - (T_ess | T_opt)

    weighted_total   = (len(T_ess) * WEIGHT_ESS) + (len(T_opt) * WEIGHT_OPT)
    weighted_matched = (len(matched_ess) * WEIGHT_ESS) + (len(matched_opt) * WEIGHT_OPT)
    weighted_missing = (len(missing_ess) * WEIGHT_ESS) + (len(missing_opt) * WEIGHT_OPT)

    overlap_score = weighted_matched / weighted_total if weighted_total else 0.0
    gap_score     = 1 - (weighted_missing / weighted_total) if weighted_total else 1.0

    return {
        "matched":       sorted(matched_ess | matched_opt),
        "missing":       sorted(missing_ess | missing_opt),
        "missing_ess":   sorted(missing_ess),
        "missing_opt":   sorted(missing_opt),
        "surplus":       sorted(surplus),
        "overlap_score": round(overlap_score, 4),
        "gap_score":     round(gap_score, 4),
    }

