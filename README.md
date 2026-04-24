# CareerVision

**Final Year Project — Faizal Ali, BSc Computer Science, Goldsmiths University of London (2026)**

---

## What it does

CareerVision is a career matching platform built for CS and tech students who want to know how well their CV actually matches the roles they're applying for — not just a vague "good luck" but a real breakdown.

There are three tools:

- **Career Explorer** — upload your CV, get a ranked list of jobs from the corpus with a CareerFit score, matched skills, missing skills, and what to do next
- **Direct Job Match** — paste a specific job description alongside your CV and get a head-to-head match report
- **Skill Tracker** — save the skills you're missing and track your progress over time (Not Started → In Progress → Done)

The scoring model (CareerFit) combines six features: TF-IDF text similarity, semantic embedding similarity, skill overlap, skill gap penalty, market relevance of missing skills, and seniority alignment. Every result shows a breakdown of what contributed what.

---

## Background

I built this as a Final Year Project worth 25% of my degree. The core problem is that students applying for jobs rarely get useful, structured feedback — they either get rejected silently or get told "add more keywords." CareerVision tries to give explainable, evidence-based feedback grounded in a real skills taxonomy (ESCO) rather than generic AI advice.

Skill extraction uses ESCO v1.2.1 (13,939 skills, 3,039 occupations). Jobs are mapped to ESCO occupations so that essential vs optional skill distinctions feed into scoring. Market relevance is computed from how often each skill appears across the job corpus within the same role family.

---

## Setup

### Requirements

- Python 3.12
- Git

### 1. Clone

```bash
git clone https://github.com/your-username/careervision.git
cd careervision
```

### 2. Virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The sentence-transformers model (~90MB) downloads automatically on first run.

### 4. Environment variables (optional)

The app runs out of the box without a `.env`. To override anything:

```bash
cp .env.example .env
# edit .env as needed
```

### 5. Set up the database

```bash
cd src
python manage.py migrate
```

### 6. Import ESCO data

Loads 13,939 skills and 3,039 occupations from the pre-built `esco.sqlite3`:

```bash
python manage.py import_esco
```

### 7. Load the job corpus

```bash
python manage.py load_jobs
```

Expected: `Jobs created: 70`

### 8. Map jobs to ESCO occupations

```bash
python manage.py map_jobs_to_esco
```

TF-IDF title matching to link each job to the closest ESCO occupation. Needed for essential/optional skill weighting.

### 9. Classify role families

```bash
python manage.py classify_role_family
```

Assigns each job to a role family (tech_software, tech_data, tech_infrastructure, non_tech). Used for market relevance scoring.

### 10. Run

```bash
python manage.py runserver
```

Go to `http://127.0.0.1:8000` and register an account.

---

## Running tests

```bash
cd src
python manage.py test
```
* To reproduce the ablation study results, run `python scripts/run_ablation.py` from the repo root (requires the full DB setup from steps 6-9 above). Prints four ranked top-10 lists — TF-IDF only, skill-only, semantic-only, and full CareerFit — against a sample CS graduate CV.*
---

## Project structure

```
CareerVision/
├── src/
│   ├── config/                     # Django settings, URLs
│   ├── core_engine/                # Pure Python pipeline — no Django imports
│   │   ├── preprocess.py           # Text normalisation
│   │   ├── retrieval.py            # TF-IDF retrieval
│   │   ├── skill_extraction.py     # Precision-first skill matching (U and T sets)
│   │   ├── skill_aliases.py        # Curated alias dict + tech seed tokens
│   │   ├── semantic_similarity.py  # Document-level semantic similarity
│   │   ├── scoring.py              # CareerFit 6-feature scoring model
│   │   ├── explanation.py          # Deterministic explanation templates
│   │   ├── market_relevance.py     # Skill frequency scoring + role family classifier
│   │   ├── comparison.py           # Shared CV↔JD comparison unit
│   │   └── text_extraction.py      # PDF/DOCX/TXT extraction
│   ├── career_explorer/            # Tool A — Career Explorer
│   │   ├── management/commands/    # import_esco, load_jobs, map_jobs_to_esco, classify_role_family
│   │   ├── services/               # careerexplorer_service.py
│   │   └── templates/
│   ├── cv_matcher/                 # Tool B — Direct Job Match
│   │   ├── services/               # cv_matcher_service.py
│   │   └── templates/
│   ├── tracker/                    # Tool C — Skill Tracker
│   ├── accounts/                   # Auth (register, login, logout, delete account)
│   └── templates/                  # Shared templates (base, index, results_viewer)
├── data/
│   ├── db/esco.sqlite3             # Pre-built ESCO database
│   ├── esco/v1_2_1/                # Raw ESCO CSV files
│   └── jobs/dummy_jobs.csv         # 70 UK graduate job descriptions
├── docs/
│   └── decision_log.md             # Every design decision, trade-off, and limitation
├── scripts/
│   ├── import_esco.py              # Standalone script to build esco.sqlite3 from raw CSVs
│   └── demo_hello_pipeline.py      # Smoke test for the core engine outside Django
├── requirements.txt
├── .env.example
└── README.md
```

---

## Design decisions

Full rationale for every choice is in `docs/decision_log.md`. Short version:

- **Django monolith** — fast delivery, easy to demo locally, ORM abstracts the DB
- **ESCO v1.2.1** — structured, free, machine-readable taxonomy with 13,939 skills and explicit occupation-skill relations
- **Two-stage retrieval** — TF-IDF shortlist first (cheap), CareerFit re-ranking second (expensive). Keeps the pipeline under 10 seconds for 70 jobs.
- **Precision-first skill extraction** — phrase-rule matching with a curated alias dict rather than single-keyword extraction from ESCO labels. Earlier approach extracted single words from verbose ESCO labels and produced "clean building facade" as a matched skill for a Python developer CV.
- **Document-level semantic embeddings** — sentence-transformers used for CV↔JD similarity at document level, not skill-level. Skill-level semantic matching against 13,939 ESCO labels produced too many false positives at any usable threshold.
- **Essential vs optional skill weighting** — ESCO records whether each skill is essential or optional for an occupation. Missing an essential skill is penalised twice as much as missing an optional one.
- **Market relevance** — missing a skill that appears in 55% of similar roles is more urgent than missing one in 5%. Feeds into both scoring and next actions priority.

---

## Known limitations

- Skill extraction is scoped to tech/CS roles. Non-tech CVs produce small or empty skill sets — this is a documented scope decision.
- ESCO occupation mapping uses TF-IDF title matching with a 0.5 threshold. Around 80% of mappings are accurate; the rest were manually corrected.
- Job corpus is static (70 UK graduate JDs). Market relevance scores are corpus-relative.
- Score ceiling is roughly 0.80 — CVs and JDs are different document formats so semantic similarity sits lower than a text-to-text match would.

---

## Test credentials

Register any account on the registration page. No pre-seeded users.

Sample inputs for testing are in `scripts/demo_hello_pipeline.py`.

## Documentation

- `docs/decision_log.md` — every design decision with rationale, trade-offs, and mitigations
- This README — setup, structure, and usage

---

## Author

**Faizal Ali**
BSc Computer Science, Goldsmiths University of London
Final Year Project, 2026
