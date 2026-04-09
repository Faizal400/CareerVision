# CareerVision — Project Decision Log
*Living document. Updated as decisions are made. Use this for your dissertation, report, and viva prep.*

---

## How to use this document
Every entry follows the same format:
- **Decision** — what was chosen
- **Why** — the reason
- **Trade-off** — what you lose
- **Mitigation** — how you reduce the loss

This can also be a viva script. When I'm asked about any part of the code and asked "why did you do it this way?", the answer could be found in here.

---

## Architecture decisions

### A1 — Django monolith over microservices
**Decision:** Single Django project with a `core_engine/` package, not separate services.
**Why:** Faster delivery within a 6-week build window. No network overhead between components. Easier to run and demonstrate locally for marking.
**Trade-off:** Harder to scale independently if one component becomes slow.
**Mitigation:** Clean service layer (`career_explorer/services/`) separates concerns — the engine could be extracted later without rewriting views.

### A2 — Separate `core_engine/` from Django apps
**Decision:** All pipeline logic (preprocessing, retrieval, skill extraction, scoring) lives in `src/core_engine/`, not inside any Django app.
**Why:** The engine is pure Python — no Django dependency. This means it can be unit tested without starting a Django server, and reused by Tool A, Tool B, and Tool C without duplication.
**Trade-off:** Slightly more import complexity (need `sys.path` awareness in scripts).
**Mitigation:** Django apps call a service layer which calls core_engine. Views never import from core_engine directly.

### A3 — SQLite for development database
**Decision:** SQLite (Django default) for the main application DB during development.
**Why:** Zero configuration, portable, sufficient for a local corpus and evaluation dataset.
**Trade-off:** Not suitable for concurrent production use.
**Mitigation:** Django's ORM abstracts the DB — switching to PostgreSQL for production requires only a settings change, no code changes.

### A4 — Tool B as shared comparison engine
**Decision:** Tool B's CV↔JD comparison logic is the atomic unit of the pipeline. Tool A loops over it; it is not a separate codebase.
**Why:** Avoids duplicating scoring, skill extraction, and explanation logic. Any improvement to the comparison engine automatically improves both tools.
**Trade-off:** Tool B's output format must be general enough for both single-JD and ranked-list contexts.
**Mitigation:** Functions return plain dicts — the caller decides how to display or rank the results.

---

## Data decisions

### D1 — ESCO v1.2.1 as skill taxonomy
**Decision:** European Skills, Competences, Qualifications and Occupations (ESCO) taxonomy as the canonical skill and occupation reference.
**Why:** Structured, machine-readable, free, and covers both occupations and skills with explicit links between them. Provides 13,939 skills and 3,039 occupations.
**Trade-off:** ESCO is EU-wide — some UK-specific terminology differs (e.g. apprenticeship structures, job title conventions).
**Mitigation:** UK-aligned job corpus supplements ESCO; alias map bridges common UK CV terminology to ESCO labels.

### D2 — Separate ESCO SQLite DB + Django import command
**Decision:** Raw ESCO data first imported into a standalone `esco.sqlite3` (via `scripts/import_esco.py`), then loaded into Django's DB via a management command (`manage.py import_esco`).
**Why:** Separation of concerns — the raw import script is reusable and independent of Django. The management command translates it into Django ORM objects.
**Trade-off:** Two-step process adds friction.
**Mitigation:** Both scripts are idempotent — running either twice produces the same result. Documented in README.

### D3 — Idempotent imports using `get_or_create`
**Decision:** All data import commands use Django's `get_or_create` rather than `bulk_create` with `ignore_conflicts`.
**Why:** `get_or_create` is explicit and readable — it clearly communicates "create if not exists" intent. Produces accurate created/skipped counts for logging.
**Trade-off:** Slower than bulk operations for very large datasets (126k relations take a few seconds).
**Mitigation:** Acceptable at this scale. Relations import runs once; subsequent runs return immediately (0 inserts).

### D4 — Local UK job corpus (CSV) over live job board scraping
**Decision:** Static CSV of job descriptions, not live scraping of job boards.
**Why:** Reproducible evaluation — the same corpus produces the same scores on every run. No scraping infrastructure or rate-limit handling needed. No legal/ToS risk.
**Trade-off:** Corpus becomes stale; does not reflect current job market in real time.
**Mitigation:** Documented as a known limitation. Evaluation is designed around the static corpus. Future work section will note live integration as an extension.

---

## Pipeline decisions

### P1 — Two-stage retrieval: TF-IDF shortlist → CareerFit re-rank
**Decision:** First retrieve Top-M candidates using TF-IDF cosine similarity, then re-rank with full CareerFit scoring.
**Why:** Running expensive scoring (skill extraction, feature computation) on every job in the corpus is wasteful. TF-IDF is fast and narrows the candidate set to the most relevant M jobs cheaply.
**Trade-off:** A relevant job could be missed if it falls outside the Top-M TF-IDF shortlist.
**Mitigation:** M is set to 10–20 (configurable), which is generous for a corpus of this size. Documented as a known limitation.

### P2 — TF-IDF with bigrams (ngram_range=(1,2))
**Decision:** TF-IDF vectoriser uses unigrams and bigrams.
**Why:** "REST API" and "data modelling" are meaningful two-word phrases — splitting them into single words loses the meaning. Bigrams capture these.
**Trade-off:** Larger vocabulary matrix; slightly slower to fit.
**Mitigation:** Corpus size is small enough that this has no measurable performance impact.

### P3 — Whole-word regex matching for skill extraction
**Decision:** Skill labels are matched in text using `\b` word boundaries (regex), not plain substring search.
**Why:** Substring search causes false positives — the skill "R" (programming language) would match inside "REST", "career", "our", etc.
**Trade-off:** Regex is slightly slower than `in` string operator.
**Mitigation:** Index is built once per request (or cached). Regex matching on a few thousand labels is fast enough for interactive use.

### P4 — Two-layer skill index: manual aliases + ESCO keyword extraction
**Decision:** Skill index is built from two sources: (1) a manually curated alias map, (2) keyword extraction from ESCO labels.
**Why:** ESCO labels are verbose phrases ("use Python scripting language") that don't match how CVs are written ("Python"). Aliases map CV vocabulary to canonical labels precisely. ESCO keyword extraction provides broader coverage.
**Trade-off:** ESCO keyword layer introduces noise — "modelling" extracted from one label can match unrelated mentions of modelling.
**Mitigation:** Alias layer takes precedence (defined first in index, not overwritten). Known noisy matches documented. Alias list expanded iteratively as false positives are spotted in testing.

### P5 — Keyword extraction uses longest non-stopword
**Decision:** When extracting a keyword from a long ESCO label, the longest word not in a stopword list is chosen.
**Why:** Longer words are more specific and less likely to false-positive. "modelling" is more discriminating than "data". First-word strategy would return stopwords or generic verbs ("use", "develop") too often.
**Trade-off:** Occasionally the longest word is still ambiguous (e.g. "techniques").
**Mitigation:** Stopword list tuned to remove common ESCO verbs. Alias layer overrides the worst cases.

### P6 — JSONField for `contrib` and `top_missing` in CareerExplorerResult
**Decision:** Feature score breakdown (`contrib`) and missing skills (`top_missing`) stored as JSON columns, not normalised tables.
**Why:** These values are always read as a complete unit — never queried field-by-field. A normalised table would add joins with no query benefit.
**Trade-off:** Cannot filter results by individual feature scores in the DB.
**Mitigation:** Acceptable for this use case — results are filtered by `fit_score` only. Full breakdown available in Python after loading.

### P7 — CareerFit scoring uses 4 of 6 planned features (2 deferred)
**Decision:** MVP CareerFit uses TF-IDF similarity, skill overlap, gap penalty, and seniority distance. Semantic embedding similarity and market relevance are deferred.
**Why:** The 4 implemented features are sufficient to produce a defensible, explainable score. Embeddings require a heavier dependency (`sentence-transformers`) and are an enhancement, not a foundation. Market relevance requires skill frequency across the corpus — meaningless until corpus reaches 50+ jobs.
**Trade-off:** Scores rely on keyword matching rather than semantic understanding — "Python developer" and "software engineer using Python" may score differently despite meaning the same thing.
**Mitigation:** Embeddings added as an explicit later upgrade with ablation showing measurable improvement over TF-IDF baseline. Market relevance added once corpus is expanded. Both framed as planned extensions in the report, not omissions.

### P8 — Semantic embeddings as Layer 3 skill matching
**Decision:** Added sentence-transformers (all-MiniLM-L6-v2) as a third layer in skill extraction. Semantic U enabled for both tools. Semantic T enabled for Tool B only.
**Why:** Keyword matching misses skills expressed differently ("build REST APIs" vs "REST API"). Embeddings match by meaning. Tool B uses real user-uploaded JDs where keyword coverage is uncertain. Tool A uses our controlled job corpus where keyword matching is sufficient for T.
**Trade-off:** 8.6s pipeline time vs 4.5s keyword-only. Threshold of 0.35 still produces some false positives in T for Tool B.
**Mitigation:** Semantic T disabled for Tool A preventing score degradation. Threshold tunable — documented in ablation study. False positives acknowledged as L2 limitation.
---

## Known limitations (honest acknowledgement — required for first-class)

| ID | Limitation | Impact | Mitigation in place |
|----|-----------|--------|-------------------|
| L1 | Job corpus is small (4 dummy jobs currently) | Evaluation is not meaningful until corpus is expanded | TODO: expand to 50–100 real UK graduate JDs before evaluation |
| L2 | Skill extraction produces false positives from ESCO keyword layer | U and T sets contain occasional irrelevant skills | Alias layer + whole-word matching reduce worst cases; documented |
| L3 | TF-IDF shortlist may miss relevant jobs ranked below Top-M | Some good matches not scored | M is generous relative to corpus size; documented |
| L4 | ESCO is EU-wide, not UK-specific | Some terminology mismatch with UK job ads | UK job corpus + alias map bridge the gap |
| L5 | No live job board integration | Corpus becomes stale | Documented as future work |

---

## Milestones completed

| Milestone | Description | Evidence |
|-----------|-------------|---------|
| M1 | ESCO data imported into Django DB | 13,939 skills, 3,039 occupations, 126,051 relations. Second run: 0 inserts (idempotent). |
| M2 | UK job corpus loaded | 4 jobs from dummy_jobs.csv. Second run: 0 inserts (idempotent). |
| M3 | TF-IDF retrieval wired into Django service layer | `/test-retrieval/` URL returns ranked jobs for any CV text input. |
| M4 | Skill extraction (U/T sets) | `/test-skills/` URL returns matched, missing, surplus skills + overlap score. False positive issue identified and mitigated with alias layer + word-boundary matching. |

---
