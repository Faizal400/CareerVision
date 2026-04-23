# src/career_explorer/views.py

from time import time

from django.shortcuts import render, redirect
from django.http import HttpResponse
from .services.careerexplorer_service import run_careerexplorer
from .forms import CareerExplorerForm
from django.contrib.auth.decorators import login_required

@login_required
def ingest(request):
    if request.method == "POST":
        form = CareerExplorerForm(request.POST, request.FILES)
        if form.is_valid():
            cv_file = form.cleaned_data.get("cv_file")
            cv_text = (form.cleaned_data.get("cv_text") or "").strip()
            experience_level = int(form.cleaned_data["experience_level"])

            # Extract text from file if uploaded, else use pasted text
            if cv_file:
                from core_engine.text_extraction import extract_cv_text
                cv_text = extract_cv_text(cv_file)
            # Store in session so results view can read it
            request.session["cv_text"] = cv_text
            request.session["experience_level"] = experience_level

            return redirect("career_explorer_results")
    else:
        form = CareerExplorerForm()

    return render(request, "career_explorer/ingest.html", {"form": form})


@login_required
def results_view(request):
    k_jobs = 10
    if request.method == "GET":
        cv_text = request.session.get("cv_text")
        experience_level = request.session.get("experience_level")
        if cv_text and experience_level is not None:
            import time
            start = time.time()
            best_k_matches = run_careerexplorer(cv_text=cv_text, user_level=experience_level, M=k_jobs)
            elapsed = time.time() - start
            print(f"Pipeline took: {elapsed:.2f}s")
            return render(request, "career_explorer/results.html", {"results": best_k_matches, "source": 0})
        else:
            return redirect("career_explorer_ingest")
    return render(request, "career_explorer/results.html")

