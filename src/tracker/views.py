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

@login_required
def plan_detail(request, plan_id):
    plan = SkillPlan.objects.filter(id=plan_id, user=request.user).first()
    if not plan:
        return HttpResponse("Plan not found", status=404)
    tracked_skills = TrackedSkill.objects.filter(plan=plan)
    return render(request, "tracker/plan_detail.html", {"plan": plan, "tracked_skills": tracked_skills})

@login_required
def update_skill_status(request, skill_id):
    if request.method == "POST":
        skill = TrackedSkill.objects.filter(id=skill_id, plan__user=request.user).first()
        if not skill:
            return HttpResponse("Skill not found", status=404)
        new_status = int(request.POST.get("skill_prog_status", skill.skill_prog_status))
        skill.skill_prog_status = new_status
        skill.save()
        return redirect("tracker_plan_detail", plan_id=skill.plan.id)
    return HttpResponse("Invalid request method", status=400)