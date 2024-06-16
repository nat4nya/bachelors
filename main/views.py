from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .decorators import group_required, logout_required, no_accepted_notes_required, no_pending_notes_required
from django.contrib.auth.models import User
from .models import Note, UsedPasswordResetToken  
from django.contrib import messages
from .models import Notification, ProfessorRequest
from django.http import HttpResponseRedirect
import logging
from .tokens import account_activation_token, reset_password_token
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password, ValidationError

logger = logging.getLogger(__name__)



# password check
def password_manual_check_home(user, old_password, new_password1, new_password2):
    if not check_password(old_password, user.password):
        return False, 'Your old password is incorrect.'
    elif new_password1 != new_password2:
        return False, 'The new passwords do not match.'
    else:
        try:
            validate_password(new_password1, user=user)
            return True, None  # Password meets requirements
        except ValidationError as e:
            return False, '\n'.join(e.messages)  # Return validation error messages

def password_manual_check_auth(user, new_password, confirm_password):
    # Check if new_password and confirm_password match
    if new_password != confirm_password:
        return False, 'The new passwords do not match.'

    # Validate the new password using Django's built-in password validation
    try:
        validate_password(new_password, user=user)
        return True, None  # Password meets requirements
    except ValidationError as e:
        return False, '\n'.join(e.messages)  # Return validation error messages

# pagina principala
@logout_required()
def main(request):
    page_name = "Pagina principală"
    return render(request, 'unauthenticated/main.html', {'page_name': page_name})


# LOGIN, REGISTER, LOGOUT
# creare useri si separarea lor pe grupuri
def reset_password_auth_action(request, uidb64, token):
    page_name = "Resetare parola"
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Decode uidb64 to get user object
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        
        if user is not None and reset_password_token.check_token(user, token):
            # Perform manual password checks
            is_valid, error_message = password_manual_check_auth(user, new_password, confirm_password)

            if not is_valid:
                messages.error(request, error_message)
            else:
                # Update user's password and save
                user.password = make_password(new_password)
                user.save()

                # Mark the token as used
                UsedPasswordResetToken.objects.create(user=user, token=token)

                messages.success(request, 'Your password has been successfully updated.')

                # Redirect to some success page or any other desired URL
                return redirect('/')  # Redirect to homepage or another page

        else:
            messages.error(request, 'Invalid password reset link. Please request a new one.')
            return redirect('/')  # Redirect to homepage or another page

    # If there are errors or the method is not POST, render the form again
    return render(request, 'unauthenticated/reset_password_page.html', {'page_name': page_name, 'uidb64': uidb64, 'token': token})


def reset_password_auth_page(request, uidb64, token):
    page_name = "Resetare parola"

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # Check if the token has already been used
    if UsedPasswordResetToken.objects.filter(user=user, token=token).exists():
        messages.error(request, 'This password reset link has already been used. Please request a new one.')
        return redirect('/')  # Redirect to homepage or another page

    return render(request, 'unauthenticated/reset_password_page.html', {'page_name': page_name, 'uidb64': uidb64, 'token': token})

def reset_password_auth(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # Perform any additional validation as needed
        if not email:
            messages.error(request, 'Email field is required.')
            return redirect('/')  # Redirect to reset password page if email is not provided

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User with that email does not exist.')
            return redirect('/')  # Redirect to reset password page if user does not exist

        # Generate password reset token
        token_generator = reset_password_token  # Use your custom token generator
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        # Construct reset password email
        mail_subject = 'Reset your password'
        message = render_to_string('unauthenticated/reset_password_email.html', {
            'user': user,
            'domain': get_current_site(request).domain,
            'uid': uid,
            'token': token,
        })
        email = EmailMessage(mail_subject, message, to=[email])
        email.send()

        # Display success message
        messages.success(request, 'An email with password reset instructions has been sent to your email address.')

        return redirect('/')  # Redirect to reset password page after sending email

    return redirect('reset_password_home')  # Redirect to reset password page if request method is not POST

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
        else:
            return reverse('main')
        

# logout
@login_required(login_url = "/login")
def log_out(request):
    logout(request)
    return redirect("/")

def activated(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account was activated. You can now log in into your account!")
    else:
        messages.error(request, "Activation link is invalid!")
    return redirect('/main')

def activateEmail(request, user, to_email):
    mail_subject = "Activate your user account"
    message = render_to_string('unauthenticated/activate_account_email.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to = [to_email])
    if email.send():
        messages.success(request, "Verification email sent successfully.")
    else:
        messages.error(request, "There was a problem sending the verification email. Please try again.")


# inregistrare
@logout_required()
def sign_up(request):
    page_name = "Înregistrare"
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('/main')
    else:
        form = RegisterForm()
    return render(request, 'unauthenticated/sign_up.html', {"form": form, "page_name": page_name})

# PAGINI PRINCIPALE
# pagina principala a studentului
@login_required(login_url='/login')
def reset_password_home(request):
    return render(request, 'main/reset_password_home.html')

@login_required(login_url='/login')
def reset_password_home_action(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # Call the password_check function
        is_valid, message = password_manual_check_home(user, old_password, new_password1, new_password2)
        
        if not is_valid:
            messages.error(request, message)
        else:
            # Update user's password
            user.set_password(new_password1)
            user.save()
            # Update session to reflect the password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been successfully updated.')
            return redirect('/')  # Redirect to home or any other page after successful password change

    return redirect('reset_password_home')  # Redirect to reset password page if form submission fails

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