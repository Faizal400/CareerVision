from django.shortcuts import render, redirect
from .forms import CVMatcherForm
from django.http import HttpResponse
from .services.cv_matcher_service import run_cvmatcher

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
                from career_explorer.services.text_extraction import extract_cv_text
                cv_text = extract_cv_text(cv_file)
                print(f"DEBUG extracted text length: {len(cv_text)}, preview: {cv_text[:100]}")
            # Store in session so results view can read it
            request.session["cv_text"] = cv_text
            request.session["experience_level"] = experience_level
            request.session["jd_text"] = jd_text
            print(f"DEBUG session cv_text length: {len(request.session.get('cv_text', ''))}")
            print(f"DEBUG session experience_level: {request.session.get('experience_level')}")
            print(f"DEBUG session jd_text: {request.session.get('jd_text', '')}")
            return redirect("cv_matcher_results")
    else:
        form = CVMatcherForm()
    return HttpResponse("CV Matcher Ingest Page - form rendering not implemented yet")

def results_view(request):
    if request.method == "GET":
        print(f"DEBUG results session cv_text: {request.session.get('cv_text', 'MISSING')[:50]}")
        print(f"DEBUG results session experience_level: {request.session.get('experience_level', 'MISSING')}")
        cv_text = request.session.get("cv_text")
        experience_level = request.session.get("experience_level")
        jd_text = request.session.get("jd_text")
        if cv_text and experience_level is not None and jd_text:
            matched_result = run_cvmatcher(cv_text, jd_text, experience_level)
            return render(request, "cv_matcher/results.html", {"results": matched_result})
        else:
            return redirect("cv_matcher_ingest")
    return render(request, "cv_matcher/results.html")