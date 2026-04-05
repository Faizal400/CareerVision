from django.urls import path
from . import views

urlpatterns = [
    path("", views.ingest, name="career_explorer_ingest"),
    path("results/", views.results_view, name="career_explorer_results"),
]