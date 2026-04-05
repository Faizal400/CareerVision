from django.db import models
from django.contrib.auth.models import User

class SkillPlan(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    plan_name = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    REFERENCE_OPTIONS = [
        (0, "Career Explorer"),
        (1, "CV Matcher")
    ]
    source = models.IntegerField(choices=REFERENCE_OPTIONS, default=0)
    class Meta:
        indexes = [models.Index(fields=["user"]),models.Index(fields=["plan_name"])]
    
    def __str__(self):
        return f"{self.plan_name} for {self.user}"

class TrackedSkill(models.Model):
    SKILL_PROGRESS_STATUS = [
        (0, "Not started"),
        (1, "In Progress"),
        (2, "Done")
    ]
    plan = models.ForeignKey(SkillPlan, null=True, blank=True,
                                        on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=200)
    skill_prog_status = models.IntegerField(choices=SKILL_PROGRESS_STATUS, default=0)
    skill_next_action = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["skill_name"]),
                   models.Index(fields=["plan"])]

    def __str__(self):
        return f"{self.skill_name} in Skill Plan ID: {self.plan}"
