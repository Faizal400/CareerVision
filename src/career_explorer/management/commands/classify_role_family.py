# src/career_explorer/management/commands/classify_role_family.py
"""
One-off script to classify the role_family field of Job entries, using ESCO occupation data
Or as a fallback if a job doesn't have an ESCO occupation, use pre-defined phrase rules to classify based on job title and description.
"""

from career_explorer.models import Job
from django.core.management.base import BaseCommand
from core_engine.preprocess import normalise_text
from core_engine.market_relevance import _classify_from_text

class Command(BaseCommand):
    help = "Add a role_family to currently existing Job entries, using ESCO occupation data or keyword-based heuristics"

    def handle(self, *args, **options):
        for job in Job.objects.filter(role_family="").select_related("esco_occupation"):
            if job.esco_occupation:
                occ_label = normalise_text(job.esco_occupation.occ_label)
                job.role_family = _classify_from_text(occ_label)
            else:
                # Fallback to keyword-based classification using title and description
                text = normalise_text(job.title + " " + job.description)
                job.role_family = _classify_from_text(text)
            job.save()
            self.stdout.write(f"Classified '{job.title}' as '{job.role_family}'")
        self.stdout.write(self.style.SUCCESS("Done."))