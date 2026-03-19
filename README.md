# CareerVision

**Final Year Project — Faizal Ali, BSc Computer Science, Goldsmiths University of London (2026)**

---

## What is CareerVision?

CareerVision is a UK-aligned career matching platform built for students and early-career graduates who struggle to understand how well their CV matches the roles they're applying for.

Most job seekers don't know which roles they're suited for, can't identify their skill gaps clearly, and get no actionable feedback from existing tools. CareerVision solves this by taking a user's CV, comparing it against a job corpus and the ESCO skills taxonomy, and returning ranked career matches with explainable scores and concrete next steps.

### The three tools

- **Tool A — Career Explorer:** Upload your CV and get a ranked list of the best matching jobs from the database, with a CareerFit score, matched skills, missing skills, and next actions for each.
- **Tool B — CV↔JD Matcher:** Paste a specific job description alongside your CV and get a direct match report — useful when you've already found a role you want.
- **Tool C — Tracker:** Save missing skills from any match result and track your progress over time (mark skills as Not Started / In Progress / Complete).

---

## Background and motivation

This project was built as a Final Year Project worth 25% of my degree. The core problem it addresses is that students applying for jobs rarely get meaningful, structured feedback — they either get rejected silently or receive vague advice. CareerVision aims to give explainable, evidence-based feedback grounded in a real skills taxonomy (ESCO) rather than generic AI advice.

---

## Key design decisions

- **Django monolith** — single project for fast delivery and easy local demonstration
- **ESCO v1.2.1 taxonomy** — 13,939 skills and 3,039 occupations with explicit skill-occupation relations
- **Two-stage retrieval** — TF-IDF shortlist for speed, CareerFit re-ranking for accuracy
- **CareerFit scoring model** — weighted combination of 4 features: text similarity (0.30), skill overlap (0.40), gap penalty (0.20), seniority alignment (0.10)
- **Deterministic explanations** — all output is template-based, not LLM-generated, ensuring reproducibility
- **Local job corpus** — static CSV of UK graduate job descriptions for reproducible evaluation

---

## Known limitations

- Job corpus is small (currently ~4 jobs) — evaluation becomes meaningful at 50+ real JDs
- Skill extraction can produce false positives from the ESCO keyword layer
- ESCO is EU-wide — some UK-specific terminology may not map perfectly
- No live job board integration — corpus is static

---

## Project structure

```
CareerVision/
├── src/                        # Django project root
│   ├── config/                 # Settings, URLs, WSGI
│   ├── career_explorer/        # Tool A — Career Explorer app
│   │   ├── management/commands/
│   │   │   ├── import_esco.py  # Load ESCO data into Django DB
│   │   │   └── load_jobs.py    # Load job corpus into Django DB
│   │   ├── services/
│   │   │   ├── careerfit_service.py   # Full Tool A pipeline
│   │   │   ├── retrieval_service.py   # TF-IDF retrieval
│   │   │   └── text_extraction.py     # PDF/DOCX/TXT extraction
│   │   ├── templates/career_explorer/
│   │   ├── models.py           # ESCOSkill, Job, CareerExplorerRun, etc.
│   │   ├── views.py
│   │   └── forms.py
│   ├── cv_matcher/             # Tool B — CV↔JD Matcher app
│   ├── tracker/                # Tool C — Skill Tracker app
│   ├── accounts/               # Auth app
│   └── core_engine/            # Pure Python pipeline (no Django dependency)
│       ├── preprocess.py       # Text normalisation
│       ├── retrieval.py        # TF-IDF retrieval
│       ├── skill_extraction.py # U/T skill set extraction
│       ├── scoring.py          # CareerFit scoring model
│       └── explanation.py      # Explanation generator
├── data/
│   ├── esco/v1_2_1/            # ESCO CSV files (not in git — see setup below)
│   │   └── engine_ready/       # Pre-cleaned ESCO CSVs
│   ├── db/                     # esco.sqlite3 (generated — not in git)
│   └── jobs/
│       └── dummy_jobs.csv      # UK job corpus
├── scripts/
│   ├── import_esco.py          # Standalone ESCO → esco.sqlite3 importer
│   └── demo_hello_pipeline.py  # Smoke test for core engine
├── docs/
│   └── decision_log.md         # All design decisions, trade-offs, limitations
├── requirements.txt
└── README.md
```

---

## Setup and installation

### Prerequisites

- Python 3.11 or 3.12 recommended (project developed on 3.14)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/careervision.git
cd careervision
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download ESCO data

Download ESCO v1.2.1 from [https://esco.ec.europa.eu/en/use-esco/download](https://esco.ec.europa.eu/en/use-esco/download).

Place the CSV files into:
```
data/esco/v1_2_1/
```

The following files are required:
- `skills_en.csv`
- `occupations_en.csv`
- `occupationSkillRelations_en.csv`

Pre-cleaned engine-ready versions must exist at:
```
data/esco/v1_2_1/engine_ready/esco_skills_clean.csv
data/esco/v1_2_1/engine_ready/esco_occupations_clean.csv
data/esco/v1_2_1/engine_ready/esco_occ_skill_clean.csv
```

### 5. Run Django migrations

```bash
cd src
python manage.py migrate
```

### 6. Import ESCO data into the standalone DB

```bash
cd ..
python scripts/import_esco.py
```

Expected output:
```
Skills: {'read': 13939, 'inserted': 13939, 'skipped': 0}
Occupations: {'read': 3039, 'inserted': 3039, 'skipped': 0}
Relations: {'read': 126051, 'inserted': 126051, ...}
```

### 7. Import ESCO data into Django's DB

```bash
cd src
python manage.py import_esco
```

Both commands are idempotent — running them twice inserts 0 duplicate rows.

### 8. Load the job corpus

```bash
python manage.py load_jobs
```

### 9. Run the development server

```bash
python manage.py runserver
```

---

## Using the application

Visit `http://127.0.0.1:8000/career-explorer/` in your browser.

### Tool A — Career Explorer

1. Upload a CV file (`.pdf`, `.docx`, or `.txt`) or paste CV text directly
2. Select your experience level
3. Click **Find My Matches**
4. View ranked job matches with CareerFit scores, matched/missing skills, and next actions

### Test URLs (development only)

| URL | Purpose |
|-----|---------|
| `/career-explorer/` | Tool A — main interface |
| `/career-explorer/results/` | Tool A — results page |
| `/test-retrieval/` | TF-IDF retrieval smoke test |
| `/test-skills/` | Skill extraction smoke test |
| `/test-careerfit/?cv=python+django+sql` | Full pipeline smoke test |
| `/admin/` | Django admin panel |

### Admin credentials

Create a superuser to access the admin panel:

```bash
python manage.py createsuperuser
```

---

## Running tests

```bash
cd src
python manage.py test
```

---

## Sample input

A sample CV (`dummy_cv.txt`) is included in the repository root for testing. Upload it via the Career Explorer form to verify the pipeline is working correctly.

---

## Dependencies — notable packages

| Package | Purpose |
|---------|---------|
| Django | Web framework |
| scikit-learn | TF-IDF vectorisation and cosine similarity |
| pandas | CSV loading and data manipulation |
| pypdf | PDF text extraction |
| python-docx | DOCX text extraction |
| sentence-transformers | Semantic embeddings (planned extension) |
| torch | Required by sentence-transformers |

---

## Documentation

- `docs/decision_log.md` — every design decision with rationale, trade-offs, and mitigations
- This README — setup, structure, and usage

---

## Author

**Faizal Ali**
BSc Computer Science, Goldsmiths University of London
Final Year Project, 2026
