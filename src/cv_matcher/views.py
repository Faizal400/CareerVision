from django.shortcuts import render, redirect
from .forms import CVMatcherForm
from django.http import HttpResponse
from .services.cv_matcher_service import run_cvmatcher
from django.contrib.auth.decorators import login_required

@login_required
def ingest(request):
    if request.method == "POST":
        form = CVMatcherForm(request.POST, request.FILES)
        if form.is_valid():
            cv_file = form.cleaned_data.get("cv_file")
            cv_text = (form.cleaned_data.get("cv_text") or "").strip()
            jd_text = form.cleaned_data["jd_text"].strip()
            experience_level = int(form.cleaned_data["experience_level"])
            # Extract text from file if uploaded, else use pasted text
            if cv_file:
                from core_engine.text_extraction import extract_cv_text
                cv_text = extract_cv_text(cv_file)
            # Store in session so results view can read it
            request.session["cv_text"] = cv_text
            request.session["experience_level"] = experience_level
            request.session["jd_text"] = jd_text
            return redirect("cv_matcher_results")
    else:
        form = CVMatcherForm()
    return render(request, "cv_matcher/ingest.html", {"form": form})

@login_required
def results_view(request):
    if request.method == "GET":
        cv_text = request.session.get("cv_text")
        experience_level = request.session.get("experience_level")
        jd_text = request.session.get("jd_text")
        if cv_text and experience_level is not None and jd_text:
            matched_result = run_cvmatcher(cv_text, jd_text, experience_level)
            return render(request, "cv_matcher/results.html", {"results": matched_result})
        else:
            return redirect("cv_matcher_ingest")
    return render(request, "cv_matcher/results.html")