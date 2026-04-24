# src/career_explorer/management/commands/map_jobs_to_esco.py

"""
This is a one-off script to populate the esco_occupation field of Job entries.

Uses TF-IDF to compare an ESCO occupation's label to the job title, and maps if there's a strong match.
This is a simple heuristic and won't be perfect, but it's a starting point for linking jobs to ESCO data.
"""

from career_explorer.models import Job, ESCOOccupation

from core_engine.retrieval import retrieve_top_m
from core_engine.preprocess import normalise_text
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Map jobs to ESCO occupations using TF-IDF title matching"

    def handle(self, *args, **options):
        occupations = list(ESCOOccupation.objects.all())
        occ_labels = [normalise_text(o.occ_label) for o in occupations]
        for job in Job.objects.filter(esco_occupation__isnull=True):
            top = retrieve_top_m(normalise_text(job.title), occ_labels, M=1)
            best_idx, best_score = top[0]
            best_match = occupations[best_idx]
            self.stdout.write(f"Job: {job.title} -> Best ESCO Match: {best_match.occ_label} (score: {best_score:.4f})")
            if best_score > 0.5:  # threshold for mapping; adjust as needed
                job.esco_occupation = best_match
                job.save()
                self.stdout.write(f"Mapped '{job.title}' to ESCO occupation '{best_match.occ_label}' with score {best_score:.4f}")
            else:
                self.stdout.write(f"No good ESCO match for '{job.title}' (best score: {best_score:.4f})")
