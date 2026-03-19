from pathlib import Path
import pandas as pd

# IMPORTANT: make sure Python can import from /src
import sys
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from core_engine.esco_loader import load_esco
from core_engine.preprocess import normalise_text
from core_engine.retrieval import retrieve_top_m

ESCO_DIR = ROOT / "data" / "esco" / "v1_2_1" / "engine_ready"
JOBS_CSV = ROOT / "data" / "jobs" / "dummy_jobs.csv"

def main():
    skill_uri_to_label, occ_uri_to_label, occ_to_skills = load_esco(ESCO_DIR)
    print(f"[ESCO loaded] skills={len(skill_uri_to_label):,} occupations={len(occ_uri_to_label):,} relations={sum(len(v) for v in occ_to_skills.values()):,}")

    jobs = pd.read_csv(JOBS_CSV, dtype=str).fillna("")
    job_texts = [normalise_text(x) for x in jobs["description"].tolist()]

    dummy_cv_text = normalise_text("python django sql git linux docker rest api")
    top = retrieve_top_m(dummy_cv_text, job_texts, M=3)

    print("\n[Top results]")
    for idx, score in top:
        row = jobs.iloc[idx]
        print(f"- {row['job_id']}: {row['title']} | tfidf={score:.3f}")

if __name__ == "__main__":
    main()