import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from career_explorer.models import ESCOSkill, ESCOSkillHierarchy

HIERARCHY_CSV = Path(__file__).resolve().parents[5] / "CareerVision" / "data" / "esco" / "v1_2_1" / "broaderRelationsSkillPillar_en.csv"

class Command(BaseCommand):
    help = "Import ESCO skill hierarchy (broader/narrower relationships)"

    def handle(self, *args, **options):
        self.stdout.write(f"Reading from: {HIERARCHY_CSV}")

        if not HIERARCHY_CSV.exists():
            self.stderr.write(f"ERROR: File not found at {HIERARCHY_CSV}")
            return

        # Build URI lookup once — avoids per-row DB queries
        skill_map = {s.skill_uri: s for s in ESCOSkill.objects.all()}
        self.stdout.write(f"Loaded {len(skill_map)} skills into memory")

        created = skipped = missing = 0

        with open(HIERARCHY_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                child_uri  = row["conceptUri"].strip()
                parent_uri = row["broaderUri"].strip()

                child  = skill_map.get(child_uri)
                parent = skill_map.get(parent_uri)

                if not child or not parent:
                    missing += 1
                    continue

                _, was_created = ESCOSkillHierarchy.objects.get_or_create(
                    parent=parent,
                    child=child,
                )
                if was_created:
                    created += 1
                else:
                    skipped += 1

        self.stdout.write(
            f"Created: {created} | Already existed: {skipped} | Skipped (missing skill): {missing}"
        )
        self.stdout.write(self.style.SUCCESS("Done."))