from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from .forms import RegisterForm, PostForm
from .models import Post

# Create your views here.

@login_required(login_url = "/login")
def home(request):
    posts = Post.objects.all()
    if request.method == "POST":
        post_id = request.POST.get("post-id")
        post = Post.objects.filter(id = post_id).first()
        if post and post.author == request.user:
            post.delete()

    return render(request, 'main/home.html', {"posts": posts})

def main(request):
    return render(request, 'main/main.html')



@login_required(login_url='/login')
def home_student(request):
    return render(request, "main/home_student.html")

@login_required(login_url='/login')
def home_professor(request):
    return render(request, "main/home_professor.html")

@login_required(login_url='/login')
def home_secretary(request):
    return render(request, "main/home_secretary.html")

@login_required(login_url = "/login")
def log_out(request):
    logout(request)
    return redirect("/login/")

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {"form": form})

@login_required(login_url = "/login")
@permission_required("main.add_post", login_url="/login", raise_exception=True)
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit = False)
            post.author = request.user
            post.save()
            return redirect("/home")
    else:
        form = PostForm()

    return render(request, 'main/create_post.html', {"form": form})

