from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_READY = REPO_ROOT / "data" / "esco" / "v1_2_1" / "engine_ready"

SKILLS_CSV = ENGINE_READY / "esco_skills_clean.csv"          # skill_uri,skill_label
OCC_CSV = ENGINE_READY / "esco_occupations_clean.csv"        # occ_uri,occ_label
REL_CSV = ENGINE_READY / "esco_occ_skill_clean.csv"          # occ_uri,skill_uri,relation_type[,skill_type]

DB_PATH = REPO_ROOT / "data" / "db" / "esco.sqlite3"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"File is empty: {path}")


def open_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS skills (
            skill_uri   TEXT PRIMARY KEY,
            skill_label TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS occupations (
            occ_uri   TEXT PRIMARY KEY,
            occ_label TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS occupation_skill (
            occ_uri       TEXT NOT NULL,
            skill_uri     TEXT NOT NULL,
            relation_type TEXT,
            skill_type    TEXT,
            PRIMARY KEY (occ_uri, skill_uri),
            FOREIGN KEY (occ_uri) REFERENCES occupations(occ_uri),
            FOREIGN KEY (skill_uri) REFERENCES skills(skill_uri)
        );

        CREATE INDEX IF NOT EXISTS idx_occskill_occ  ON occupation_skill(occ_uri);
        CREATE INDEX IF NOT EXISTS idx_occskill_skill ON occupation_skill(skill_uri);
        """
    )
    conn.commit()


def count_rows(conn: sqlite3.Connection) -> dict[str, int]:
    out: dict[str, int] = {}
    for table in ["skills", "occupations", "occupation_skill"]:
        out[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0])
    return out


def clean(x: str | None) -> str:
    return (x or "").strip()


def read_dict_rows(csv_path: Path) -> tuple[list[str], Iterable[dict[str, str]]]:
    """
    Reads CSV rows as dictionaries with:
      - utf-8-sig (safe if BOM ever appears)
      - stripped header names and stripped values
    Returns (fieldnames, row_iterable)
    """
    f = csv_path.open("r", encoding="utf-8-sig", newline="")
    reader = csv.DictReader(f)
    # Normalise fieldnames: strip whitespace
    if reader.fieldnames is None:
        f.close()
        raise ValueError(f"CSV has no header row: {csv_path}")

    fieldnames = [fn.strip() for fn in reader.fieldnames]

    def row_iter() -> Iterable[dict[str, str]]:
        try:
            for raw in reader:
                # Strip keys + values
                out: dict[str, str] = {}
                for k, v in raw.items():
                    if k is None:
                        continue
                    out[k.strip()] = clean(v)
                yield out
        finally:
            f.close()

    return fieldnames, row_iter()


def import_skills(conn: sqlite3.Connection, csv_path: Path) -> dict[str, int]:
    inserted = 0
    skipped = 0
    read = 0

    fieldnames, rows = read_dict_rows(csv_path)
    log(f"Skills CSV headers: {fieldnames}")

    for row in rows:
        read += 1
        skill_uri = clean(row.get("skill_uri"))
        skill_label = clean(row.get("skill_label"))

        if not skill_uri or not skill_label:
            skipped += 1
            continue

        cur = conn.execute(
            "INSERT OR IGNORE INTO skills(skill_uri, skill_label) VALUES (?, ?);",
            (skill_uri, skill_label),
        )
        inserted += cur.rowcount

    return {"read": read, "inserted": inserted, "skipped": skipped}


def import_occupations(conn: sqlite3.Connection, csv_path: Path) -> dict[str, int]:
    inserted = 0
    skipped = 0
    read = 0

    fieldnames, rows = read_dict_rows(csv_path)
    log(f"Occupations CSV headers: {fieldnames}")

    for row in rows:
        read += 1
        occ_uri = clean(row.get("occ_uri"))
        occ_label = clean(row.get("occ_label"))

        if not occ_uri or not occ_label:
            skipped += 1
            continue

        cur = conn.execute(
            "INSERT OR IGNORE INTO occupations(occ_uri, occ_label) VALUES (?, ?);",
            (occ_uri, occ_label),
        )
        inserted += cur.rowcount

    return {"read": read, "inserted": inserted, "skipped": skipped}


def import_relations(conn: sqlite3.Connection, csv_path: Path) -> dict[str, int]:
    inserted = 0
    skipped_empty = 0
    skipped_fk = 0
    read = 0

    # Build parent sets so we can avoid FK failures (and log what was skipped)
    occ_set = {r[0] for r in conn.execute("SELECT occ_uri FROM occupations;")}
    skill_set = {r[0] for r in conn.execute("SELECT skill_uri FROM skills;")}

    fieldnames, rows = read_dict_rows(csv_path)
    log(f"Relations CSV headers: {fieldnames}")

    for row in rows:
        read += 1
        occ_uri = clean(row.get("occ_uri"))
        skill_uri = clean(row.get("skill_uri"))
        relation_type = clean(row.get("relation_type"))
        skill_type = clean(row.get("skill_type"))  # optional

        if not occ_uri or not skill_uri:
            skipped_empty += 1
            continue

        # Filter out any relation whose parents don't exist in our imported subset
        if occ_uri not in occ_set or skill_uri not in skill_set:
            skipped_fk += 1
            continue

        cur = conn.execute(
            """
            INSERT OR IGNORE INTO occupation_skill
            (occ_uri, skill_uri, relation_type, skill_type)
            VALUES (?, ?, ?, ?);
            """,
            (occ_uri, skill_uri, relation_type, skill_type),
        )
        inserted += cur.rowcount

    return {"read": read, "inserted": inserted, "skipped_empty": skipped_empty, "skipped_fk": skipped_fk}


def main() -> None:
    # Guardrails
    require_file(SKILLS_CSV)
    require_file(OCC_CSV)
    require_file(REL_CSV)

    log(f"DB: {DB_PATH}")
    log(f"ENGINE_READY: {ENGINE_READY}")

    conn = open_db(DB_PATH)
    try:
        create_schema(conn)

        before = count_rows(conn)
        log(f"Before: {before}")

        log("Importing skills...")
        s = import_skills(conn, SKILLS_CSV)
        conn.commit()
        log(f"Skills: {s}")

        log("Importing occupations...")
        o = import_occupations(conn, OCC_CSV)
        conn.commit()
        log(f"Occupations: {o}")

        log("Importing occupation-skill relations...")
        r = import_relations(conn, REL_CSV)
        conn.commit()
        log(f"Relations: {r}")

        after = count_rows(conn)
        log(f"After: {after}")

        log("SUCCESS: Run again. Second run should insert ~0 new rows (idempotent).")

    finally:
        conn.close()


if __name__ == "__main__":
    main()