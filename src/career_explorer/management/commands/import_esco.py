# src/career_explorer/management/commands/import_esco.py

import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand

from career_explorer.models import ESCOSkill, ESCOOccupation, OccupationSkillRelation


# Path to your existing esco.sqlite3 (the one import_esco.py already populated)
ESCO_DB = Path(__file__).resolve().parents[5] / "CareerVision" / "data" / "db" / "esco.sqlite3"


class Command(BaseCommand):
    help = "Import ESCO skills, occupations, and relations into Django DB."

    def handle(self, *args, **options):
        self.stdout.write(f"Reading from: {ESCO_DB}")

        if not ESCO_DB.exists():
            self.stderr.write(f"ERROR: esco.sqlite3 not found at {ESCO_DB}")
            self.stderr.write("Fix: run `python scripts/import_esco.py` first.")
            return

        conn = sqlite3.connect(ESCO_DB)
        conn.row_factory = sqlite3.Row  # lets you access columns by name

        try:
            self._import_skills(conn)
            self._import_occupations(conn)
            self._import_relations(conn)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS("Done."))

    # ------------------------------------------------------------------
    # Step 1: skills
    # ------------------------------------------------------------------
    def _import_skills(self, conn):
        rows = conn.execute("SELECT skill_uri, skill_label FROM skills;").fetchall()
        self.stdout.write(f"Skills in source DB: {len(rows):,}")

        created = 0
        for row in rows:
            _, was_created = ESCOSkill.objects.get_or_create(
                skill_uri=row["skill_uri"],
                defaults={"skill_label": row["skill_label"]},
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Skills created: {created:,}  |  already existed: {len(rows) - created:,}")

    # ------------------------------------------------------------------
    # Step 2: occupations
    # ------------------------------------------------------------------
    def _import_occupations(self, conn):
        rows = conn.execute("SELECT occ_uri, occ_label FROM occupations;").fetchall()
        self.stdout.write(f"Occupations in source DB: {len(rows):,}")

        created = 0
        for row in rows:
            _, was_created = ESCOOccupation.objects.get_or_create(
                occ_uri=row["occ_uri"],
                defaults={"occ_label": row["occ_label"]},
            )
            if was_created:
                created += 1

        self.stdout.write(f"  Occupations created: {created:,}  |  already existed: {len(rows) - created:,}")

    # ------------------------------------------------------------------
    # Step 3: relations
    # ------------------------------------------------------------------
    def _import_relations(self, conn):
        rows = conn.execute(
            "SELECT occ_uri, skill_uri, relation_type FROM occupation_skill;"
        ).fetchall()
        self.stdout.write(f"Relations in source DB: {len(rows):,}")

        # Build lookup dicts so we don't hit the DB inside the loop
        skill_map = {s.skill_uri: s for s in ESCOSkill.objects.all()}
        occ_map   = {o.occ_uri:   o for o in ESCOOccupation.objects.all()}

        created = skipped = 0
        for row in rows:
            occ   = occ_map.get(row["occ_uri"])
            skill = skill_map.get(row["skill_uri"])

            if not occ or not skill:
                skipped += 1
                continue

            relation_type = row["relation_type"] or OccupationSkillRelation.ESSENTIAL

            _, was_created = OccupationSkillRelation.objects.get_or_create(
                occupation=occ,
                skill=skill,
                defaults={"relation_type": relation_type},
            )
            if was_created:
                created += 1

        self.stdout.write(
            f"  Relations created: {created:,}  |  skipped (missing parent): {skipped:,}"
        )