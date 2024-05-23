from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm

# Create your views here.

@login_required(login_url = "/login")

def home(request):
    return render(request, 'main/home.html')

def main(request):
    return render(request, 'main/main.html')

def log_out(request):
    logout(request)
    return redirect("/login/")

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/main')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {"form": form})