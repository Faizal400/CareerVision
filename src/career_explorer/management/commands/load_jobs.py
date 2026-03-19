# src/career_explorer/management/commands/load_jobs.py

import pandas as pd
from pathlib import Path

from django.core.management.base import BaseCommand

from career_explorer.models import Job

JOBS_CSV = Path(__file__).resolve().parents[5] / "CareerVision" / "data" / "jobs" / "dummy_jobs.csv"


class Command(BaseCommand):
    help = "Load the UK job corpus from CSV into Django's Job model."

    def handle(self, *args, **options):
        self.stdout.write(f"Reading from: {JOBS_CSV}")

        if not JOBS_CSV.exists():
            self.stderr.write(f"ERROR: CSV not found at {JOBS_CSV}")
            return

        df = pd.read_csv(JOBS_CSV, dtype=str).fillna("")
        self.stdout.write(f"Rows in CSV: {len(df):,}")

        created = skipped = 0

        for _, row in df.iterrows():
            job_id = row["job_id"].strip()
            if not job_id:
                skipped += 1
                continue

            _, was_created = Job.objects.get_or_create(
                job_id=job_id,
                defaults={
                    "title":           row.get("title", "").strip(),
                    "location":        row.get("location", "").strip(),
                    "description":     row.get("description", "").strip(),
                    "company":         row.get("company", "").strip(),
                    "seniority_level": int(row["seniority_level"])
                                       if row.get("seniority_level", "").strip().isdigit()
                                       else 1,
                    "role_family":     row.get("role_family", "").strip(),
                },
            )
            if was_created:
                created += 1

        self.stdout.write(
            f"  Jobs created: {created:,}  |  already existed: {len(df) - created - skipped:,}  |  skipped: {skipped:,}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))