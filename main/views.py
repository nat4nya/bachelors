from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .decorators import group_required, logout_required
from django.contrib.auth.models import User
from .models import Note
from django.contrib import messages





# pagina principala
def main(request):
    return render(request, 'main/main.html')

# LOGIN, REGISTER, LOGOUT
# creare useri si separarea lor pe grupuri
class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='student').exists():
            return reverse('home_student')
        elif user.groups.filter(name='secretary').exists():
            return reverse('home_secretary')
        elif user.groups.filter(name='professor').exists():
            return reverse('home_professor')

# logout
@login_required(login_url = "/login")
def log_out(request):
    logout(request)
    return redirect("/login/")

# inregistrare
@logout_required()
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





# PAGINI PRINCIPALE
# pagina principala a studentului
@login_required(login_url='/login')
@group_required('student')
def home_student(request):
    accepted_request = Note.objects.filter(author=request.user, is_accepted=True).exists()
    if accepted_request:
        return redirect('home_student_accepted')
    else:
        notes_sent = Note.objects.filter(author=request.user, is_refused=False)
        return render(request, 'main/home_student.html', {'notes_sent': notes_sent})

# pagina principala a profesorului
@login_required(login_url='/login')
@group_required('professor')
def home_professor(request):
    professor = request.user
    # Filter out refused notes
    notes_received = Note.objects.filter(destination=professor, is_refused=False)
    return render(request, "main/home_professor.html", {'notes_received': notes_received})

# pagina principala a secretarei
@login_required(login_url='/login')
@group_required('secretary')
def home_secretary(request):
    secretary_department_group = request.user.groups.exclude(name='secretary').first()
    professors = User.objects.filter(groups__name='professor').filter(groups=secretary_department_group)
    accepted_notes = Note.objects.filter(destination__in=professors, is_accepted=True)

    return render(request, "main/home_secretary.html", {'professors': professors, 'accepted_notes': accepted_notes})
def accept_note(request, note_id):
    if request.method == 'POST':
        note = Note.objects.get(pk=note_id)
        note.is_accepted = True
        note.save()
    return redirect('home_professor')  # Redirect back to the professor's home page





# CERERI DE LICENTA/DISERATIE
# crearea cererii
@login_required(login_url='/login')
@group_required('student')
def create_note(request):
    user_department_group = request.user.groups.exclude(name='student').first()
    professors = User.objects.filter(groups__name='professor')
    same_dep_professors = [prof for prof in professors if prof.groups.exclude(name='professor').first() == user_department_group]

    if request.method == 'POST':
        form = NoteForm(request.POST, request=request)
        if form.is_valid():
            professor_id = request.POST.get('destination')
            if professor_id:
                professor = get_object_or_404(User, id=professor_id)
                author = request.user
                
                # Check if the maximum limit for sending requests to a professor has been reached
                if Note.objects.filter(author=author, destination=professor).count() >= 5:
                    return redirect("create_note")  # Redirect back to the create_note page if the limit is reached
                
                note = form.save(commit=False)
                note.author = author
                note.destination = professor
                note.save()
                return redirect("/home-student")
    else:
        form = NoteForm(request=request)

    return render(request, 'notes/create_note.html', {"form": form, "professors": same_dep_professors})

@login_required(login_url='/login')
@group_required('student')
def home_student_accepted(request):
    accepted_note = Note.objects.filter(author=request.user, is_accepted=True)
    return render(request, 'main/accepted_request.html', {'accepted_notes': accepted_note})

def refuse_note(request, note_id):
    if request.method == 'POST':
        note = Note.objects.get(pk=note_id)
        note.is_refused = True
        note.save()
    return redirect('home_professor')  # Redirect back to the professor's home page
