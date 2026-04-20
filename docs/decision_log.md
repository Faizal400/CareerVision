# CareerVision — Decision Log
*I'm keeping this as a living document throughout the build. Every time I make a real decision — not just "I wrote some code" but "I chose X over Y and here's why" — it goes in here. This will feed directly into my report and viva prep.*

---

Every entry follows the same format:
- **Decision** — what I chose
- **Why** — the actual reason
- **Trade-off** — what I'm giving up
- **Mitigation** — how I'm managing that loss

---

## Architecture

### A1 — Django monolith, not microservices
**Decision:** Single Django project with a `core_engine/` package handling all pipeline logic.
**Why:** I had a tight build window and didn't want to spend half of it setting up service communication. A monolith lets me move fast, run everything locally, and demo it easily for marking. There's no real argument for microservices at this scale.
**Trade-off:** If one part of the pipeline gets slow, it affects everything. Not easy to scale components independently.
**Mitigation:** I built a clean service layer (`career_explorer/services/`, `cv_matcher/services/`) that separates concerns properly. The engine could be extracted later without touching views.

### A2 — `core_engine/` is pure Python, separate from Django apps
**Decision:** All the actual pipeline logic — preprocessing, retrieval, skill extraction, scoring — lives in `src/core_engine/`. No Django imports in there.
**Why:** I wanted the engine to be testable without spinning up a Django server, and reusable across Tool A, B, and C without duplicating code. If I'd put the logic inside Django apps it would've been a mess.
**Trade-off:** Slightly more complex import structure.
**Mitigation:** Django apps talk to a service layer, service layer talks to core_engine. Views never import from core_engine directly. Clean chain.

### A3 — SQLite for now
**Decision:** Using Django's default SQLite DB for development.
**Why:** Zero config, portable, works fine for a local corpus and evaluation. Doesn't need a server running.
**Trade-off:** Not production-ready. Can't handle concurrent writes.
**Mitigation:** Django ORM abstracts everything — if I ever needed PostgreSQL it's a one-line settings change, no code rewrite.

### A4 — `compare_cv_to_jd` is the shared atomic unit
**Decision:** Tool A and Tool B both call the same `compare_cv_to_jd` function. Tool A loops it over many jobs; Tool B calls it once.
**Why:** Avoids having two separate scoring/skill extraction codebases that drift apart. Any fix or improvement to the comparison engine automatically improves both tools. DRY in practice, not just in theory.
**Trade-off:** The return format has to work for both single-JD and ranked-list contexts.
**Mitigation:** The function returns a plain dict. The caller decides how to display or rank it.

---

## Data

### D1 — ESCO v1.2.1 as the skill taxonomy
**Decision:** Using ESCO as the canonical reference for skills and occupations.
**Why:** It's structured, free, machine-readable, and covers 13,939 skills and 3,039 occupations with explicit links between them. Nothing else at this scale is freely available and this well-organised.
**Trade-off:** ESCO is EU-wide. Some UK-specific terminology differs — job title conventions, qualification names, etc.
**Mitigation:** UK-aligned job corpus supplements ESCO. The alias map bridges common UK CV vocabulary to ESCO labels directly.

### D2 — Two-step ESCO import (standalone script → Django management command)
**Decision:** Raw ESCO data imported into a standalone `esco.sqlite3` first, then pulled into Django via `manage.py import_esco`.
**Why:** Separation of concerns. The raw import script is reusable outside Django. The management command translates it into ORM objects.
**Trade-off:** Two steps adds a bit of friction.
**Mitigation:** Both are idempotent — running either twice gives the same result. Documented clearly.

### D3 — `get_or_create` for all imports
**Decision:** Import commands use `get_or_create` rather than `bulk_create`.
**Why:** It's explicit — clearly communicates "create if not exists". Gives accurate created/skipped counts so I can verify imports ran correctly.
**Trade-off:** Slower than bulk operations. The 126k occupation-skill relations take a few seconds.
**Mitigation:** Acceptable at this scale. Imports run once; after that, subsequent runs return immediately.

### D4 — Static UK job corpus, not live scraping
**Decision:** CSV of 70 UK graduate job descriptions, not live scraping.
**Why:** Reproducible evaluation. The same corpus gives the same scores on every run. No scraping infrastructure, no rate limits, no legal risk.
**Trade-off:** Corpus goes stale. Doesn't reflect live market.
**Mitigation:** Documented as a known limitation. Live integration is a clear future work item.

---

## Pipeline

### P1 — Two-stage retrieval: TF-IDF shortlist → CareerFit re-rank
**Decision:** First shortlist Top-M jobs using TF-IDF cosine similarity, then re-rank with full CareerFit scoring.
**Why:** Running full CareerFit scoring on every job in the corpus is wasteful. TF-IDF is fast and cheap — it narrows the candidate set to the most relevant M jobs before the expensive stuff runs.
**Trade-off:** A relevant job could be missed if it falls outside Top-M in the TF-IDF shortlist.
**Mitigation:** M is configurable and set generously relative to corpus size. Documented as a known limitation.

### P2 — TF-IDF with bigrams
**Decision:** TF-IDF vectoriser uses `ngram_range=(1,2)` — unigrams and bigrams.
**Why:** "REST API" and "data modelling" are two-word phrases with specific meanings. Treating them as individual words loses that. Bigrams capture these.
**Trade-off:** Larger vocabulary matrix, slightly slower to fit.
**Mitigation:** Corpus is small enough that this has no measurable performance impact.

### P3 — Precision-first phrase matching (replaces keyword extraction)
**Decision:** Replaced single-keyword ESCO extraction with full phrase-rule matching. ESCO labels are only included if they pass a tech-seed filter and have 2+ meaningful tokens. Multi-word phrases matched as exact substrings; single-word aliases matched with word boundaries.
**Why:** The previous approach extracted one keyword from long ESCO labels — e.g. "clean" from "clean building facade". This caused catastrophic false positives: any JD mentioning "clean interfaces" or "clean code" would match "clean building facade" as a skill. I tested it with a real CV and real JD and the output was unusable. Credibility matters more than recall here. A small, correct skill set beats a large, wrong one.
**Trade-off:** Lower recall. Skills not covered by aliases or tech-like ESCO phrases won't be detected.
**Mitigation:** Alias list expanded iteratively as gaps are spotted in testing. ESCO phrase layer still provides broader coverage for tech skills. Limitation documented honestly.

### P4 — Two-layer skill matching: curated aliases + ESCO phrase filter
**Decision:** Skill matching uses: (1) manually curated alias map as primary layer, (2) tech-filtered ESCO phrase matching as secondary layer.
**Why:** ESCO labels are verbose and formal ("use Python scripting language"). CVs and JDs write "Python". Aliases bridge this gap precisely. ESCO phrases provide coverage for multi-word technical concepts that aliases don't cover.
**Trade-off:** Alias layer requires manual maintenance. Anything not in aliases or passing the ESCO filter is missed.
**Mitigation:** Alias list is the first thing I expand when I spot a miss in testing. ESCO filter is intentionally conservative — better to miss something than to match garbage.

### P5 — ESCO phrase filter: tech-seed tokens + banned domain tokens
**Decision:** ESCO labels only enter the phrase matching layer if they contain a recognised tech-seed token (e.g. "kubernetes", "python", "docker") and have no banned domain tokens (e.g. "timber", "facade", "artist").
**Why:** Without this filter, ESCO's 13,939 labels include thousands of non-tech skills that produce false positives. "Clean building facade" is a real ESCO skill — it has no place appearing in a software engineering match.
**Trade-off:** The tech-seed list is CS-focused. Non-CS roles produce smaller T sets.
**Mitigation:** Documented as a known scope limitation. The architecture is extensible — adding seeds for other domains requires only expanding the `TECH_SEED_TOKENS` set.

### P6 — JSONField for contrib and top_missing
**Decision:** Feature score breakdown (`contrib`) and missing skills stored as JSON columns, not normalised tables.
**Why:** These are always read as a complete unit — never queried field-by-field. A normalised table would add joins with no benefit.
**Trade-off:** Can't filter results by individual feature scores at the DB level.
**Mitigation:** Fine for this use case — results are ranked by `fit_score` only.

### P7 — CareerFit: 5 features with documented weights
**Decision:** CareerFit uses five weighted features: tfidf (0.10), semantic (0.40), overlap (0.25), gap (0.20), seniority (0.05). Weights sum to 1.0.
**Why:** Each feature captures a different signal. Semantic similarity (0.40) gets the highest weight because it's the most robust — it handles synonyms and paraphrasing that keyword matching misses. Overlap and gap (0.25 + 0.20) together give the skill-level signal. TF-IDF (0.10) is kept as a transparent baseline. Seniority (0.05) is a realism constraint.
**Trade-off:** Weights are hand-tuned, not learned from data. Different weight distributions might perform better.
**Mitigation:** Ablation study documents the effect of each feature. Weights are explicit and tunable — changing them is a one-line edit backed by evaluation evidence.

### P8 — Semantic embeddings at document level, not skill level
**Decision:** Used `sentence-transformers` (all-MiniLM-L6-v2) to compute one CV embedding vs one JD embedding. Cosine similarity becomes the `semantic` feature in CareerFit scoring. Semantic skill extraction (matching CV/JD text against 13,939 ESCO labels) was tried and abandoned.
**Why:** Document-level semantic similarity is stable and meaningful — both documents are describing a professional profile vs a job requirement. Skill-level semantic matching against 13,939 ESCO labels at any reasonable threshold produced catastrophic false positives. At threshold 0.35, skills like "clean building facade" matched from a Python developer CV because the model found vague semantic connections. Tested at 0.50 and 0.65 — still too noisy or returned nothing useful. The approach was fundamentally wrong for this use case.
**Trade-off:** Document-level similarity doesn't distinguish between "I use Python" and "the role requires Python" — it treats the whole document as a blob.
**Mitigation:** Skill-level signals (overlap, gap) handle the structured skill reasoning. Semantic handles meaning at the macro level. The two complement each other.

### P9 — Seniority inference for Tool B
**Decision:** For Tool B (user-pasted JD), seniority level is inferred from JD text using keyword heuristics rather than hardcoded.
**Why:** The previous implementation hardcoded `job_level=1` for every Tool B comparison. A senior Core AI infrastructure role isn't a graduate role. This made the seniority feature meaningless for Tool B.
**Trade-off:** Keyword heuristics can be wrong — a JD mentioning "senior" in passing might not be a senior role.
**Mitigation:** Default fallback is Mid-level (2) — a reasonable assumption when the JD doesn't signal level clearly. Documented as an approximation.

---

## Known Limitations

| ID | Limitation | Impact | Mitigation |
|----|-----------|--------|------------|
| L1 | Alias dict and tech-seed tokens are CS-focused | Non-CS roles produce smaller T sets and weaker skill gap signals | Documented scope. Architecture is extensible — domain seeds can be added without structural changes |
| L2 | Precision-recall trade-off in skill extraction | Some real skills missed if not in alias dict or ESCO phrase filter | Alias list expanded iteratively as gaps spotted in testing |
| L3 | TF-IDF shortlist may miss jobs outside Top-M | Some matches not scored | M is generous relative to corpus size |
| L4 | ESCO is EU-wide, not UK-specific | Terminology mismatch with some UK job ads | UK corpus + alias map bridge the gap |
| L5 | No live job board integration | Corpus becomes stale | Future work — documented |
| L6 | Score ceiling ~0.80 | CV and JD are different document formats — semantic similarity is naturally moderate even for good matches | Expected behaviour, documented |
| L7 | Small T sets for non-standard roles (e.g. data architecture) | Skill gap signals less informative | Expand SKILL_ALIASES with domain-specific terms |

---

## Milestones

| Milestone | Description | Evidence |
|-----------|-------------|---------|
| M1 | ESCO data imported | 13,939 skills, 3,039 occupations, 126,051 relations. Idempotent — second run: 0 inserts |
| M2 | UK job corpus loaded | 70 jobs from dummy_jobs.csv across STEM and non-STEM roles |
| M3 | TF-IDF retrieval | Two-stage pipeline working: shortlist → CareerFit re-rank |
| M4 | Skill extraction (U/T sets) | Precision-first phrase matching. Before/after ablation documented |
| M5 | CareerFit scoring | 5-feature weighted model. Weights documented and justified |
| M6 | Explanation generator | Deterministic templates — reproducible, defensible |
| M7 | Tool A end-to-end | Upload CV → ranked results with scores, matched/missing skills, next actions |
| M8 | Tool B end-to-end | Paste CV + JD → single match report with seniority inference |
| M9 | Tool C — Skill Tracker | Save missing skills to plans, update status, dashboard + plan detail |
| M10 | Auth | Login, logout, register. `@login_required` on all tool views |
| M11 | Semantic embeddings | Document-level semantic similarity added as CareerFit feature. Ablation vs keyword-only documented |
| M12 | Precision-first patch | Rewrote skill extraction after live testing revealed catastrophic false positives. Before/after results documented |
