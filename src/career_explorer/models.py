from django.db import models
from django.contrib.auth.models import User

class ESCOSkill(models.Model):
    skill_uri   = models.CharField(max_length=300, unique=True)
    skill_label = models.CharField(max_length=300)

    class Meta:
        indexes = [models.Index(fields=["skill_label"])]

    def __str__(self):
        return self.skill_label


class ESCOOccupation(models.Model):
    occ_uri   = models.CharField(max_length=300, unique=True)
    occ_label = models.CharField(max_length=300)

    def __str__(self):
        return self.occ_label


class OccupationSkillRelation(models.Model):
    ESSENTIAL = "essential"
    OPTIONAL  = "optional"
    RELATION_CHOICES = [(ESSENTIAL, "Essential"), (OPTIONAL, "Optional")]

    occupation    = models.ForeignKey(ESCOOccupation, on_delete=models.CASCADE,
                                      related_name="skill_relations")
    skill         = models.ForeignKey(ESCOSkill, on_delete=models.CASCADE,
                                      related_name="occupation_relations")
    relation_type = models.CharField(max_length=20, choices=RELATION_CHOICES,
                                     default=ESSENTIAL)

    class Meta:
        unique_together = ("occupation", "skill")

    def __str__(self):
        return f"{self.occupation} → {self.skill} ({self.relation_type})"


class Job(models.Model):
    SENIORITY_CHOICES = [
        (0, "Intern / Placement"),
        (1, "Graduate / Junior"),
        (2, "Mid"),
        (3, "Senior"),
        (4, "Lead"),
    ]

    job_id          = models.CharField(max_length=50, unique=True)
    title           = models.CharField(max_length=200)
    company         = models.CharField(max_length=200, blank=True)
    location        = models.CharField(max_length=200, blank=True)
    description     = models.TextField()
    seniority_level = models.IntegerField(choices=SENIORITY_CHOICES, default=1)
    role_family     = models.CharField(max_length=100, blank=True)
    esco_occupation = models.ForeignKey(ESCOOccupation, null=True, blank=True,
                                        on_delete=models.SET_NULL)

    class Meta:
        indexes = [models.Index(fields=["seniority_level"]),
                   models.Index(fields=["role_family"])]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class CareerExplorerRun(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at       = models.DateTimeField(auto_now_add=True)
    experience_level = models.IntegerField(default=1)
    cv_text_stored   = models.BooleanField(default=False)

    def __str__(self):
        return f"Run #{self.pk} by {self.user} at {self.created_at:%Y-%m-%d %H:%M}"


class CareerExplorerResult(models.Model):
    run         = models.ForeignKey(CareerExplorerRun, on_delete=models.CASCADE,
                                    related_name="results")
    job         = models.ForeignKey(Job, on_delete=models.CASCADE)
    fit_score   = models.FloatField()
    top_missing = models.JSONField(default=list)
    contrib     = models.JSONField(default=dict)
    rank        = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"Result: {self.job.title} | score={self.fit_score:.2f}"