from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .decorators import group_required, logout_required, no_accepted_notes_required, no_pending_notes_required
from django.contrib.auth.models import User
from .models import Note
from django.contrib import messages
from .models import Notification, ProfessorRequest
from django.http import HttpResponseRedirect
import logging
logger = logging.getLogger(__name__)




# pagina principala
@logout_required()
def main(request):
    page_name = "Pagina principală"
    return render(request, 'unauthenticated/main.html', {'page_name': page_name})



# LOGIN, REGISTER, LOGOUT
# creare useri si separarea lor pe grupuri
class CustomLoginView(LoginView):
    template_name = 'unauthenticated/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = "Autentificare"  # Set the page name here
        return context

    def get_success_url(self):
        user = self.request.user
        if user.groups.filter(name='student').exists():
            if Note.objects.filter(author=user, is_accepted=True).exists():
                return reverse('home_student_accepted')  # Redirect to accepted notes page
            else: 
                return reverse('home_student')
        elif user.groups.filter(name='secretar').exists():
            return reverse('home_secretary')
        elif user.groups.filter(name='profesor').exists():
            professor_request, created = ProfessorRequest.objects.get_or_create(professor=user)
            if created:
                professor_request.save()
            return reverse('home_professor')
        

# logout
@login_required(login_url = "/login")
def log_out(request):
    logout(request)
    return redirect("/")

# inregistrare
@logout_required()
def sign_up(request):
    page_name = "Înregistrare"
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/main')
    else:
        form = RegisterForm()
    return render(request, 'unauthenticated/sign_up.html', {"form": form, "page_name": page_name})





# PAGINI PRINCIPALE
# pagina principala a studentului
@login_required(login_url='/login')
@group_required('student')
@no_accepted_notes_required
def home_student(request):
    accepted_request = Note.objects.filter(author=request.user, is_accepted=True).exists()
    notifications = Notification.objects.filter(note__author=request.user)
    if accepted_request:
        return redirect('home_student_accepted')
    else:
        notes_sent = Note.objects.filter(author=request.user, is_refused=False)
        return render(request, 'main/home_student.html', {'notes_sent': notes_sent, 'notifications': notifications})

# pagina principala a profesorului
@login_required(login_url='/login')
@group_required('profesor')
def home_professor(request):
    professor = request.user
    notes_received = Note.objects.filter(destination=professor, is_refused=False).select_related('author')
    professor_request = ProfessorRequest.objects.get(professor=request.user)

    show_remove_button = not professor_request.no_requests
    show_add_button = professor_request.no_requests
    
    if request.method == 'POST':
        form = request.POST
        note_id = request.GET.get('note_id')
        reason = form.get('reason')

        if note_id and reason:
            try:
                # Get the note and mark it as refused
                note = get_object_or_404(Note, pk=note_id)
                note.is_refused = True
                note.save()

                # Create a notification for the student
                Notification.objects.create(note=note, reason=reason)
                
                # Redirect back to the professor's home page
                return HttpResponseRedirect(reverse('home_professor'))
            except Exception as e:
                # Log any exceptions that occur
                logger.exception("An error occurred while processing the rejection request.")
                # Optionally, display an error message to the user
                messages.error(request, "An error occurred while processing the rejection request. Please try again.")
                # Redirect back to the professor's home page
                return HttpResponseRedirect(reverse('home_professor'))

    return render(request, "main/home_professor.html", {
        'notes_received': notes_received,
        "show_remove_button": show_remove_button,
        "show_add_button": show_add_button,})


# pagina principala a secretarei
@login_required(login_url='/login')
@group_required('secretar')
def home_secretary(request):
    secretary_department_group = request.user.groups.exclude(name='secretar').first()
    professors = User.objects.filter(groups__name='profesor').filter(groups=secretary_department_group)
    accepted_notes = Note.objects.filter(destination__in=professors, is_accepted=True)

    return render(request, "main/home_secretary.html", {'professors': professors, 'accepted_notes': accepted_notes})
def accept_note(request, note_id):
    if request.method == 'POST':
        note = get_object_or_404(Note, pk=note_id)
        note.is_accepted = True
        note.save()

        # Update other notes of the same author that are not accepted
        other_notes = Note.objects.filter(author=note.author, is_accepted=False, is_refused=False)
        for other_note in other_notes:
            other_note.is_refused = True
            other_note.save()

    return redirect('home_professor')  # Redirect back to the professor's home page





# CERERI DE LICENTA/DISERATIE
# crearea cererii
from .models import ProfessorRequest

@login_required(login_url='/login')
@group_required('student')
def create_note(request):
    user_department_group = request.user.groups.exclude(name='student').first()
    
    # Fetch professors excluding those with no_requests=True
    professors = User.objects.filter(groups__name='profesor').exclude(professorrequest__no_requests=True)
    
    # Filter professors by department group
    same_dep_professors = [prof for prof in professors if prof.groups.exclude(name='profesor').first() == user_department_group]

    if request.method == 'POST':
        form = NoteForm(request.POST, request=request)
        if form.is_valid():
            professor_id = request.POST.get('destination')
            if professor_id:
                professor = get_object_or_404(User, id=professor_id)
                author = request.user
                
                # Check if the maximum limit for sending requests to a professor has been reached
                if Note.objects.filter(author=author, destination=professor).count() >= 3:
                    form_errors = "You have already sent 3 requests to this professor."
                else:
                    note = form.save(commit=False)
                    note.author = author
                    note.destination = professor
                    note.save()
                    return redirect("/home-student")
        else:
            form_errors = "Please correct the errors below."
    else:
        form = NoteForm(request=request)
        form_errors = None

    return render(request, 'notes/create_note.html', {"form": form, "professors": same_dep_professors, "form_errors": form_errors})




@login_required(login_url='/login')
@group_required('student')
@no_pending_notes_required
def home_student_accepted(request):
    accepted_note = Note.objects.filter(author=request.user, is_accepted=True)
    return render(request, 'notes/accepted.html', {'accepted_notes': accepted_note})

@login_required
def refuse_note(request, note_id):
    if request.method == 'POST':
        note_id = request.POST.get('note_id')
        reason = request.POST.get('reason', '')

        if note_id:
            try:
                # Get the note and mark it as refused
                note = Note.objects.get(pk=note_id)
                note.is_refused = True
                note.save()

                # Create a notification for the student
                Notification.objects.create(note=note, reason=reason)

                messages.success(request, "Note rejected successfully.")
            except Note.DoesNotExist:
                messages.error(request, "Note does not exist.")
            except Exception as e:
                messages.error(request, "An error occurred while processing the rejection request. Please try again.")

    return HttpResponseRedirect(reverse('home_professor'))

def refuse_all_requests(request):
    # Get all notes for the current professor where is_accepted is False and is_refused is False
    notes_to_refuse = Note.objects.filter(destination=request.user, is_accepted=False, is_refused=False)
    try:
        # Update all filtered notes to set is_refused = True
        notes_to_refuse.update(is_refused=True)
    except Exception as e:
        messages.error(request, f"There was an error refusing the requests: {str(e)}")

    return redirect('home_professor')

@group_required('profesor')
@login_required
def remove_myself(request):
    if request.method == 'POST':
        try:
            professor_request = ProfessorRequest.objects.get(professor=request.user)
            professor_request.no_requests = True
            professor_request.save()
            messages.success(request, "You were removed successfully!")
        except ProfessorRequest.DoesNotExist:
            messages.error(request, "Professor request not found.")
    
    return redirect(reverse('home_professor'))

@group_required('profesor')
@login_required
def add_myself(request):
    if request.method == 'POST':
        try:
            professor_request = ProfessorRequest.objects.get(professor=request.user)
            professor_request.no_requests = False
            professor_request.save()
            messages.success(request, "You were added successfully!")
        except ProfessorRequest.DoesNotExist:
            messages.error(request, "Professor request not found.")
    
    return redirect(reverse('home_professor'))