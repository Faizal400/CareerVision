from pathlib import Path
import pandas as pd

def load_esco(engine_ready_dir: Path):
    skills = pd.read_csv(engine_ready_dir / "esco_skills_clean.csv", dtype=str)
    occs = pd.read_csv(engine_ready_dir / "esco_occupations_clean.csv", dtype=str)
    rel = pd.read_csv(engine_ready_dir / "esco_occ_skill_clean.csv", dtype=str)

    skill_uri_to_label = dict(zip(skills["skill_uri"], skills["skill_label"]))
    occ_uri_to_label = dict(zip(occs["occ_uri"], occs["occ_label"]))

    occ_to_skills = {}
    for occ_uri, g in rel.groupby("occ_uri"):
        occ_to_skills[occ_uri] = g["skill_uri"].tolist()

    return skill_uri_to_label, occ_uri_to_label, occ_to_skills