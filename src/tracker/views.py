# tracker/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import SkillPlan, TrackedSkill
from core_engine.explanation import _next_action
@login_required
def save_tskill_toplan(request):
    if request.method == "POST":
        plan_name = request.POST.get("plan_name")
        source = int(request.POST.get("source", 0))
        skill_names = request.POST.getlist("skills")  # getlist for checkboxes
        if not plan_name or not skill_names:
            return redirect("career_explorer_ingest")  # or show an error
        plan, created = SkillPlan.objects.get_or_create(plan_name=plan_name, user=request.user, source=source)
        for tSkill in skill_names:
            next_action = _next_action(tSkill)
            TrackedSkill.objects.get_or_create(
                plan=plan,
                skill_name=tSkill,
                defaults = {"skill_next_action": next_action}
            )

        return redirect("tracker_dashboard")
    return HttpResponse("Invalid request method", status=400)

@login_required
def tracker_dashboard(request):
    plans = SkillPlan.objects.filter(user=request.user).order_by("-plan_name", "-date_created")
    return render(request, "tracker/dashboard.html", {"plans": plans})