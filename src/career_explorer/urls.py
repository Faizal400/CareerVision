from django.urls import path
from . import views

urlpatterns = [
    path("test-retrieval/", views.test_retrieval, name="test_retrieval"),
    path("test-skills/", views.test_skills, name="test_skills"),
    path("test-careerfit/", views.test_careerfit, name="test_careerfit"),
    path("", views.ingest, name="career_explorer_ingest"),
    path("results/", views.results_view, name="career_explorer_results"),
]