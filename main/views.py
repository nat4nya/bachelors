from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView
from .decorators import group_required, logout_required
from django.contrib.auth.models import User, Group
from .models import Note





# pagina principala
@logout_required()
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
    notes_sent = Note.objects.filter(author=request.user)
    professors = User.objects.filter(groups__name='professor')
    return render(request, 'main/home_student.html', {'professors': professors, 'notes_sent': notes_sent})

# pagina principala a profesorului
@login_required(login_url='/login')
@group_required('professor')
def home_professor(request):
    professor = request.user
    notes_received = Note.objects.filter(destination=professor)
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
def reject_note(request, note_id):
    if request.method == 'POST':
        note = get_object_or_404(Note, pk=note_id)
        note.delete()
    return redirect('home_professor')  # Redirect back to the professor's home page





# CERERI DE LICENTA/DISERATIE
# crearea cererii
@login_required(login_url='/login')
@group_required('student')
def create_note(request):
    user_department_group = request.user.groups.exclude(name='student').first()
    professors = User.objects.filter(groups__name='professor')
    same_dep_professors = []

    for professor in professors:
        second_group = professor.groups.exclude(name='professor').first()
        if second_group == user_department_group:
            same_dep_professors.append(professor)

    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            
            # Check if professor ID is provided and valid
            professor_id = request.POST.get('destination')
            if professor_id:
                professor = get_object_or_404(User, id=professor_id)
                note.destination = professor
                note.save()
                return redirect("/home-student")
            else:
                # Handle case where professor ID is not provided
                # You can display an error message or redirect the user to an appropriate page
                pass
    else:
        form = NoteForm()
    
    return render(request, 'main/create_note.html', {"form": form, "professors": same_dep_professors})





