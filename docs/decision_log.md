# CareerVision - Decision Log
*This is a living record of every real decision I made during the build. Not a polished report - more like a journal I kept alongside the code. When a supervisor asks "why did you do it this way?", the answer is in here.*

---

## How to read this

Every entry has:
- **What I decided** - the actual choice
- **Why** - the real reason, not the cleaned-up version
- **What I gave up** - honest trade-off
- **How I'm managing that** - mitigation

Entries are roughly chronological. Later entries sometimes contradict earlier ones - that's intentional. This is a build log, not a design document written after the fact.

---

## The beginning - March 2026

Came into this with a solid idea on paper and a Django background but no experience with NLP, text similarity, or taxonomies. The spec was more detailed than my ability to execute it.

Supervisor's feedback on the brief (60%) and design doc (66%) both said the same thing: the project needs to actually *use* ML/AI, not just describe it. Components are clear but algorithmic depth isn't there. That set the tone for everything.

The governing question throughout: what's the minimum I need to do to make this computationally defensible, end-to-end working, and actually useful?

---

## Architecture

### A1 - Django monolith, not microservices

**What I decided:** Single Django project. Everything lives together.

**Why:** Tight build window, limited experience. Microservices would have meant spending the first two weeks on infrastructure. Django gives me ORM, auth, sessions, templates, and forms in one place. Running locally for a demo is one command.

**What I gave up:** Can't scale components independently. If the ML part gets slow, it affects everything.

**How I'm managing that:** Clean service layer separates concerns. `core_engine/` has no Django imports - pure Python, could be extracted later without touching views.

---

### A2 - `core_engine/` separated from Django apps

**What I decided:** All pipeline logic lives in `src/core_engine/` as pure Python. Views never touch core_engine directly. The chain is always: view → service → core_engine.

**Why:** Testable without starting a Django server. Both Tool A and Tool B reuse the same comparison logic - which they do through `comparison.py`.

**What I gave up:** Slightly more complex import structure.

**How I'm managing that:** The three-layer pattern is consistent throughout. Documented in the project structure.

---

### A3 - SQLite for everything

**What I decided:** SQLite as the DB for both development and ESCO import.

**Why:** Zero config. Portable. Works on any machine without installing a DB server. Right tool for a local demo.

**What I gave up:** Not suitable for concurrent production use.

**How I'm managing that:** Django's ORM abstracts the database - switching to PostgreSQL is a one-line settings change. Documented as a known limitation.

---

### A4 - `compare_cv_to_jd` as the shared atomic unit

**What I decided:** Tool A and Tool B both call the same `compare_cv_to_jd` function. Tool A loops it. Tool B calls it once.

**Why:** When building Tool B, I was about to duplicate all the scoring logic from Tool A. That was the moment I extracted `comparison.py`. Any improvement to the comparison engine now automatically improves both tools.

**What I gave up:** Return format has to work for both single-JD and ranked-list contexts.

**How I'm managing that:** The function returns a plain dict. The caller decides how to display or rank results.

---

## Data

### D1 - ESCO v1.2.1 as the skill taxonomy

**What I decided:** Use ESCO as the canonical reference rather than building my own taxonomy.

**Why:** Structured, free, machine-readable, 13,939 skills and 3,039 occupations with explicit occupation-skill relations. Nothing else at this scale is freely available and this well-organised. It also gives me a defensible data source - I didn't make these skills up.

**What I gave up:** ESCO is EU-wide. Some UK-specific terminology doesn't map perfectly.

**How I'm managing that:** UK-aligned job corpus supplements ESCO. Alias map bridges common UK CV vocabulary to ESCO labels directly.

---

### D2 - Two-step ESCO import

**What I decided:** Raw ESCO data first imported into `esco.sqlite3` via `scripts/import_esco.py`, then pulled into Django's DB via `manage.py import_esco`.

**Why:** Separation of concerns. The raw import script works without Django. The management command translates it into ORM objects. Both are idempotent.

**What I gave up:** Two steps add friction for a new setup.

**How I'm managing that:** Both steps idempotent. Documented clearly in the README.

---

### D3 - `get_or_create` for all imports

**What I decided:** All import commands use `get_or_create` rather than `bulk_create`.

**Why:** Explicit. Produces accurate created/skipped counts for verification. Clear intent.

**What I gave up:** Slower than bulk operations. 126k relations take a few seconds.

**How I'm managing that:** Acceptable at this scale. Imports run once.

---

### D4 - Static UK job corpus, not live scraping

**What I decided:** 70 UK graduate job descriptions in a CSV. No live scraping.

**Why:** Reproducible evaluation. Same corpus gives same scores on every run. No scraping infrastructure, no rate limits, no legal risk.

**What I gave up:** Corpus goes stale. Doesn't reflect the live job market.

**How I'm managing that:** Documented as a known limitation. Live integration is explicitly identified as future work.

---

## Pipeline

### P1 - Two-stage retrieval: TF-IDF shortlist → CareerFit re-rank

**What I decided:** First shortlist top-M jobs via TF-IDF cosine similarity, then re-rank with full CareerFit scoring.

**Why:** Running full CareerFit on 70 jobs every request was 8+ seconds. TF-IDF narrows the candidate set cheaply before the expensive stuff runs.

**Performance profiling (70 jobs):**
- TF-IDF retrieval: 0.02s
- Skill index build (cold): 0.18s → (warm/cached): 0.00s
- CareerFit loop: ~8-9s with semantic, ~4s keyword-only

**What I gave up:** A relevant job could fall outside top-M and never get scored.

**How I'm managing that:** M is set generously relative to corpus size. Documented as L3.

---

### P2 - TF-IDF with bigrams

**What I decided:** `ngram_range=(1,2)` - unigrams and bigrams.

**Why:** "REST API" and "data modelling" are two-word phrases with specific meanings. Bigrams capture these. Unigrams alone would split them.

**What I gave up:** Larger vocabulary matrix, slightly slower.

**How I'm managing that:** Corpus small enough that performance impact is unmeasurable.

---

### P3 - Keyword extraction approach (initial) - abandoned

*This was the first approach. It failed badly. Keeping it here because the failure led to the current design.*

**What I tried:** Extract a single keyword from each ESCO skill label using `_extract_keyword`. Strategy: longest non-stopword from the label. "use Python scripting language" → "python".

**What actually happened:** Catastrophic false positives. "clean building facade" → keyword "clean". Any CV or JD mentioning "clean code" or "clean interfaces" triggered "clean building facade" as a matched skill. A Python developer CV matched "sell processed timber in a commercial environment".

I didn't discover this by reading the code carefully - I discovered it on 15 April when I actually tested the system with a real CV and a real JD from G-Research. The output was embarrassing. Before that I'd been testing with toy inputs that didn't trigger the worst cases.

That test was the turning point. The whole skill extraction layer needed a rewrite.

---

### P4 - Initial CareerFit: 4 features, then evolved to 6

**Starting weights:**

| Feature | Initial | Final |
|---------|---------|-------|
| TF-IDF | 0.30 | 0.10 |
| Skill overlap | 0.40 | 0.25 |
| Gap penalty | 0.20 | 0.10 |
| Seniority | 0.10 | 0.05 |
| Semantic | - | 0.40 |
| Market relevance | - | 0.10 |

**Why the weights shifted:** Semantic got added with 0.40 because it's the most robust signal - handles synonyms and paraphrasing that keyword matching misses. TF-IDF dropped because it's a baseline, not the main driver. Gap dropped because the essential/optional weighting now does the heavy lifting there.

Weights are hand-tuned, not learned. The ablation study provides evidence that the final configuration outperforms simpler alternatives.

---

### P5 - In-memory caching for skill index and ML models

**What I decided:** Django `locmem` cache for phrase rules, sentence-transformers model, and skill frequency dicts.

**Why:** First request builds everything. Subsequent requests return instantly. Without caching, loading 13,939 ESCO skills on every request would make the system unusable.

**Why locmem over Redis:** Zero config for local development. Cache lost on server restart - acceptable for demo.

**What I gave up:** Not persistent. Server restart clears everything.

**How I'm managing that:** Documented. Redis would replace locmem with a one-line settings change in production.

---

### P6 - Deterministic explanations, not LLM-generated

**What I decided:** All explanation text is template-based. `NEXT_ACTIONS` is a dict mapping skill labels to concrete advice. Summaries are f-strings built from computed values. No free-form generation.

**Why:** Reproducibility. Same inputs always produce same output. I can defend every sentence by pointing to a computed value. Markers can verify the output is consistent.

**What I gave up:** Less fluent, less varied output.

**How I'm managing that:** The structured breakdown (CareerFit score, feature contributions, matched/missing skills) compensates. Users get data they can act on.

---

### P7 - JSONField for contrib and debug data

**What I decided:** Feature score breakdowns and debug rows stored as JSON in the result dict rather than normalised tables.

**Why:** Always read as a complete unit, never queried field-by-field. Normalised tables would add joins with no benefit.

**What I gave up:** Can't filter results by individual feature scores at DB level.

**How I'm managing that:** Results always retrieved by fit_score. Field-level filtering was never a use case.

---

### P8 - Precision-first skill extraction (major rework, April)

**What triggered this:** Real CV + real JD test. "clean building facade", "sell processed timber", "propose projects to artist" as matched skills for a Python developer. Score 0.16. Missing skills showed empty despite skill coverage of 0.13.

**What I changed:**

Replaced `_extract_keyword` with `_build_phrase_rules()` - a list of `PhraseRule` objects:
- Layer 1: curated `SKILL_ALIASES` dict (manually maintained, highest precision)
- Layer 2: ESCO labels passing tech-seed filter - must contain a `TECH_SEED_TOKENS` token, must have 2+ meaningful tokens, must have no banned domain tokens

Matching:
- Multi-word phrases: exact substring in normalised text
- Single tokens: word boundary regex (`\b`) to prevent partial matches

**Before vs after (same CV + Core AI JD):**
- Before: matched "clean building facade", "timber". Score: 0.16. Missing: empty (lie).
- After: matched Python, Docker, APIs. Missing: Kubernetes, Terraform, CI/CD. Score: 0.36. No garbage.

**Why precision over recall:** Credibility matters more than coverage. A smaller correct set beats a large wrong set. One "clean building facade" destroys trust in everything.

**What I gave up:** Lower recall. Non-tech CVs produce small or empty skill sets.

**How I'm managing that:** Alias list expanded iteratively. Scope limitation documented. System explicitly scoped to CS/tech graduate roles.

---

### P9 - Semantic embeddings at document level, not skill level

**What I tried first:** sentence-transformers matching CV text against 13,939 ESCO skill labels at threshold 0.35.

**What happened:** The model found vague semantic connections between a Python developer CV and skills like "clean building facade", "nursing", "timber" - because the CV's general meaning overlapped weakly with hundreds of irrelevant ESCO skills. Tried 0.50 and 0.65. Either same noise appeared or nothing matched.

**Root cause:** Encoding a whole CV as one vector and comparing it against short 3-5 word ESCO phrases is unreliable. The CV's meaning is a mixture of many topics and a short phrase can accidentally score high against part of that mixture.

**What I decided instead:** Document level. One CV embedding vs one JD embedding. Cosine similarity becomes the `semantic` feature, weighted at 0.40.

**Why this works better:** Both documents describe a professional profile vs a job requirement. Document-level similarity is more stable.

**Trade-off I accepted:** Doesn't distinguish "I use Python" from "the role requires Python". The skill features (overlap, gap) handle structured skill reasoning. Semantic handles meaning at the macro level.

---

### P10 - Semantic T disabled for Tool A, enabled for Tool B

**What I decided:** Tool A uses semantic only for U. T stays keyword-only. Tool B uses semantic for both U and T.

**Why Tool A:** My job corpus is 70 structured JDs. They're well-covered by the alias dict. Adding semantic to T for Tool A inflated required skill sets with false positives. Ablation showed Junior Backend dropped from 0.77 to 0.44 when semantic T was enabled at threshold 0.35.

**Why Tool B:** User pastes any JD. Keyword coverage is uncertain. Semantic T helps when the JD uses different wording than the alias dict.

**Implementation:** `use_semantic_T: bool = False` in `compare_cv_to_jd`. Tool A passes False. Tool B passes True.

---

### P11 - Essential vs optional skill weighting

**What I decided:** When a job is mapped to an ESCO occupation, split T into essential skills (T_ess, weight 2) and optional skills (T_opt, weight 1) using `OccupationSkillRelation.relation_type`.

**Why:** Missing "Python" for a software developer role (essential) is more serious than missing "Ansible" (optional). Flat weighting treated all required skills equally.

**Implementation challenge:** ESCO stores verbose labels like "Python (computer programming)" but my alias dict produces "Python". Direct set intersection returned almost nothing.

**Fix:** Run `extract_skills()` on each ESCO skill label to normalise it, then intersect with T.

**Fallback:** When no occupation mapping exists (Tool B, or unmapped jobs), T_opt = set() and the formula degrades gracefully to flat scoring.

---

### P12 - ESCO occupation mapping via TF-IDF title matching

**What I decided:** Map each job to an ESCO occupation using TF-IDF similarity between job title and ESCO occupation label. Threshold: 0.5. Management command: `map_jobs_to_esco`.

**Results:** 54/70 jobs mapped. 16 unmapped.

**Known bad mappings:**
- "Graduate Scrum Master" → "fisheries master" (shares "master")
- "Graduate HR Advisor" → "tax advisor" (shares "advisor")
- "Graduate Data Architect" → "architect" (too broad)
- "Graduate PR Executive" → "executive assistant" (shares "executive")

Manual corrections applied for the worst cases via Django shell.

**Why I kept automated mapping despite imperfections:** ~80% accuracy is better than zero. Bad mappings affect a small subset and only influence essential/optional weighting - not the core score. Documented honestly.

---

### P13 - Role family classification

**What I decided:** Two-stage automatic classification - ESCO occupation label matching (primary), keyword fallback (secondary). Four categories: tech_software, tech_data, tech_infrastructure, non_tech.

**Why:** Market relevance needs to compare skill frequency within the same type of role. Python appearing in 55% of tech jobs is meaningful. Python appearing in 55% of all jobs (including nursing and teaching) is diluted.

**Known issue:** Single-word keywords like "analyst" are ambiguous. "Graduate Financial Analyst" classified as tech_data. 22 manual corrections needed after the automated run.

**Documented limitation:** A production-scale fix would use zero-shot classification using sentence-transformers against role family labels. Out of scope for this submission - documented as future work.

---

### P14 - Market relevance as CareerFit feature

**What I decided:** 6th CareerFit feature. For each missing skill, look up corpus frequency within same role family. Average, invert. 1.0 means missing only rare skills (good), 0.0 means missing very common skills (bad).

**Secondary use:** `_priority_missing` sorts missing skills by market relevance before selecting top 2 for next actions. DevOps results correctly surface Kubernetes and Terraform as priority gaps rather than alphabetically first skills.

**Known limitation:** When no skills match at all, market_relevance still contributes ~0.09 because it's based on missing skill frequencies. Slightly inflates very weak matches. Documented.

---

### P15 - ESCO hierarchy traversal - investigated and abandoned

**What I investigated:** `broaderRelationsSkillPillar_en.csv` - parent-child skill relationships. The idea: JavaScript partially satisfying a TypeScript requirement because TypeScript is a child of JavaScript.

**What I found:** 6,460 relations imported. Query results:

```
advise others → 270 children
think critically → 182 children
lead others → 143 children
```

The hierarchy models generic competency relationships, not technical skill taxonomies. "JavaScript → TypeScript" doesn't exist. Both are siblings under "computer programming".

**Decision:** Reverted the model and migration. Documented as investigated future work. A custom technical hierarchy would be required - out of scope.

---

### P16 - Ablation study

Ran four CareerFit configurations against the same CV across 10 jobs:

| Configuration | Junior Backend | Data Scientist | Ranking quality |
|---|---|---|---|
| TF-IDF only | 0.137 | 0.053 | Poor - Data Governance ranked 3rd |
| Skill features only | 0.846 | 0.416 | Good - correct ordering |
| Semantic only | 0.568 | 0.610 | Poor - scores bunched, Backend ranked 6th |
| Full CareerFit | 0.771 | 0.585 | Best - correct ranking, differentiated |

**Key findings:**

TF-IDF alone: wrong ranking. Data Governance ranked above Data Scientist for a Python developer.

Semantic alone: scores bunched 0.54-0.65 with almost no differentiation. Junior Backend dropped to 6th place despite being a near-perfect skill match. Document-level semantic can't distinguish a perfect match from a weak match without structured skill signals.

Skill features alone: correct ranking. But no semantic understanding.

Full CareerFit: best ranking. Semantic handles meaning, skill features handle precision, market relevance prioritises important gaps. Neither TF-IDF nor semantic alone is sufficient - the combination is required.

**Note**
These results are reproducible - `scripts/run_ablation.py` runs all four configurations against the same sample CV and prints the ranked lists. Requires the full DB setup (jobs loaded, ESCO imported, roles mapped and classified).

---

### P17 - Shared results template (DRY)

**What I decided:** Extract shared results display logic into `src/templates/results_viewer.html`. Both Tool A and Tool B results templates become thin wrappers. Tool B's view wraps its single result in a list.

**Why:** Both results templates were ~95% identical. Copy-pasting fixes in one required updating the other.

**Side effect fixed:** `source` was hardcoded as 1 in the shared template initially. Fixed by passing it as context from each view - 0 for Tool A, 1 for Tool B.

---

## Known Limitations

| ID | Limitation | Impact | Mitigation |
|----|-----------|--------|------------|
| L1 | Skill extraction scoped to CS/tech roles | Non-tech CVs produce empty skill sets | Documented scope decision |
| L2 | Precision-recall trade-off | Some real skills missed | Alias list expanded iteratively |
| L3 | TF-IDF shortlist may miss jobs outside top-M | Some matches not scored | M is generous |
| L4 | ESCO is EU-wide | Some UK terminology mismatch | UK corpus + alias map |
| L5 | Static job corpus | Corpus becomes stale | Future work |
| L6 | Score ceiling ~0.80 | CV and JD are different document formats | Expected, documented |
| L7 | Small T sets for non-standard roles | Skill gap signals less informative | Expand SKILL_ALIASES |
| L8 | ESCO occupation mapping ~80% accurate | Essential/optional weighting wrong for ~20% of jobs | Manual corrections; documented |
| L9 | Role family classification has edge cases | Misclassifications for ambiguous titles | 22 manual corrections; future fix is zero-shot classifier |
| L10 | Market relevance inflates score for zero-skill matches | Very weak matches score slightly higher | Documented |
| L11 | ESCO skill hierarchy unsuitable for technical partial credit | "JavaScript → TypeScript" doesn't exist in ESCO | Custom technical hierarchy needed; future work |

---

## Milestones

| Milestone | Evidence |
|-----------|---------|
| M1 - ESCO imported | 13,939 skills, 3,039 occupations, 126,051 relations. Idempotent. |
| M2 - Job corpus loaded | 70 UK graduate JDs across STEM and non-STEM |
| M3 - TF-IDF retrieval | Two-stage pipeline working |
| M4 - Skill extraction | Precision-first. Before/after ablation documented. |
| M5 - CareerFit scoring | 6-feature weighted model. Ablation across 4 configurations. |
| M6 - Explanation generator | Deterministic templates. Market relevance drives next action priority. |
| M7 - Tool A end-to-end | Upload CV → ranked results |
| M8 - Tool B end-to-end | Paste CV + JD → match report with seniority inference |
| M9 - Tool C Skill Tracker | Save missing skills, update status, dashboard |
| M10 - Auth | Login, logout, register. Data isolation verified. |
| M11 - Semantic embeddings | Document-level. Ablation vs keyword-only documented. |
| M12 - Precision-first patch | Rewrote skill extraction after live test showed false positives |
| M13 - Essential/optional weighting | ESCO relation_type used to weight T_ess 2× vs T_opt |
| M14 - Market relevance | 6th CareerFit feature. Role family scoped. |
| M15 - ESCO occupation mapping | 54/70 jobs mapped via TF-IDF title matching |
| M16 - Role family classification | Two-stage classification. 4 categories. |
| M17 - ESCO hierarchy traversal | Investigated and abandoned - generic competencies, not technical |
| M18 - Shared results template | DRY'd Tool A and B results display |
| M19 - Ablation study | 4 configurations tested. Full CareerFit outperforms all subsets. |