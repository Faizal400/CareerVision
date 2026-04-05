from django.urls import path
from . import views

from django.contrib.auth import views as auth_views
TEMPLATES_FOLDER = "accounts/"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name=f"{TEMPLATES_FOLDER}/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("profile/", views.profile, name="profile"),
    path("delete_account/", views.delete_account, name="delete_account"),
]