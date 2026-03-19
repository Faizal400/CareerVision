# src/career_explorer/views.py

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .services.retrieval_service import get_top_jobs
from .services.careerfit_service import run_careerfit
from core_engine.skill_extraction import _build_skill_index, build_U_T, skill_gap_summary
from .forms import CareerExplorerForm

def ingest(request):
    if request.method == "POST":
        form = CareerExplorerForm(request.POST, request.FILES)
        if form.is_valid():
            cv_file = form.cleaned_data.get("cv_file")
            cv_text = (form.cleaned_data.get("cv_text") or "").strip()
            experience_level = int(form.cleaned_data["experience_level"])

            # Extract text from file if uploaded, else use pasted text
            if cv_file:
                from career_explorer.services.text_extraction import extract_cv_text
                cv_text = extract_cv_text(cv_file)
                print(f"DEBUG extracted text length: {len(cv_text)}, preview: {cv_text[:100]}")
            # Store in session so results view can read it
            request.session["cv_text"] = cv_text
            request.session["experience_level"] = experience_level
            print(f"DEBUG session cv_text length: {len(request.session.get('cv_text', ''))}")
            print(f"DEBUG session experience_level: {request.session.get('experience_level')}")

            return redirect("career_explorer_results")
    else:
        form = CareerExplorerForm()

    return render(request, "career_explorer/ingest.html", {"form": form})


def results_view(request):
    k_jobs = 10
    if request.method == "GET":
        print(f"DEBUG results session cv_text: {request.session.get('cv_text', 'MISSING')[:50]}")
        print(f"DEBUG results session experience_level: {request.session.get('experience_level', 'MISSING')}")
        cv_text = request.session.get("cv_text")
        experience_level = request.session.get("experience_level")
        if cv_text and experience_level is not None:
            best_k_matches = run_careerfit(cv_text=cv_text, user_level=experience_level, M=k_jobs)
            return render(request, "career_explorer/results.html", {"results": best_k_matches})
        else:
            return redirect("career_explorer_ingest")
    return render(request, "career_explorer/results.html")


def test_retrieval(request):
    cv_text = request.GET.get("cv", "python django sql git linux docker rest api")

    results = get_top_jobs(cv_text, M=4)

    lines = [f"<h2>Top matches for: '{cv_text}'</h2>"]
    for job, score in results:
        lines.append(f"<p><b>{job.title}</b> @ {job.location} — score: {score:.3f}</p>")

    return HttpResponse("\n".join(lines))

def test_skills(request):
    cv_text = request.GET.get("cv", "Python Django SQL Git Linux Docker REST API data modelling")
    job_text = request.GET.get("job", "Python SQL ETL pipelines Airflow data modelling PostgreSQL")

    skill_index = _build_skill_index()
    U, T = build_U_T(cv_text, job_text, skill_index)
    summary = skill_gap_summary(U, T)

    lines = [
        f"<h2>Skill extraction test</h2>",
        f"<p><b>Skill index size:</b> {len(skill_index):,}</p>",
        f"<p><b>U (your skills):</b> {sorted(U)}</p>",
        f"<p><b>T (job wants):</b> {sorted(T)}</p>",
        f"<p><b>Matched:</b> {summary['matched']}</p>",
        f"<p><b>Missing:</b> {summary['missing']}</p>",
        f"<p><b>Overlap score:</b> {summary['overlap_score']}</p>",
    ]

    return HttpResponse("\n".join(lines))

from .services.careerfit_service import run_careerfit

def test_careerfit(request):
    cv_text    = request.GET.get("cv", "Python Django SQL Git Linux Docker REST API data modelling")
    user_level = int(request.GET.get("level", 1))

    results = run_careerfit(cv_text, user_level=user_level)

    lines = ["<h2>CareerFit results</h2>"]
    for rank, r in enumerate(results, start=1):
        exp = r["explanation"]
        lines.append("<hr>")
        lines.append(f"<h3>#{rank} {r['job'].title} — {exp['fit_percent']}%</h3>")
        lines.append(f"<p>{exp['summary']}</p>")
        lines.append(f"<p><b>Top reasons:</b> {exp['top_reasons']}</p>")
        lines.append(f"<p><b>Missing:</b> {exp['top_missing']}</p>")
        lines.append(f"<p><b>Next actions:</b></p>")
        for action in exp["next_actions"]:
            lines.append(f"<p>→ {action}</p>")

    return HttpResponse("\n".join(lines))