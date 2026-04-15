from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

TEMPLATES_FOLDER = "accounts/"

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("profile")
    elif request.method == "GET":
        form = UserCreationForm()
    return render(request, f"{TEMPLATES_FOLDER}/register.html", {"form": form})

@login_required
def profile(request):
    return render(request, f"{TEMPLATES_FOLDER}/profile.html")

@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        user.delete()
        return redirect("login")
    return render(request, f"{TEMPLATES_FOLDER}/delete_acc_confirm.html")

@login_required
def home(request):
    return render(request, "index.html", {"user": request.user})