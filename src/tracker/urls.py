# tracker/urls.py
from django.urls import path
from . import views

urlpatterns = [
     path("save/", views.save_tskill_toplan, name="save_tskill_toplan"),
      path("dashboard/", views.tracker_dashboard, name="tracker_dashboard"),
      path("plan/<int:plan_id>/", views.plan_detail, name="tracker_plan_detail"),
      path("update_skill_status/<int:skill_id>/", views.update_skill_status, name="tracker_update_skill_status")
]