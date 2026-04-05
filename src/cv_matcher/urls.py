from django.urls import path
from . import views

urlpatterns = [
    path("", views.ingest, name="cv_matcher_ingest"),
    path("results/", views.results_view, name="cv_matcher_results"),
]