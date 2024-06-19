# toate librariile de care e nevoie
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoteForm
from django.urls import reverse
from django.contrib.auth.views import LoginView
from .decorators import group_required, logout_required, no_accepted_notes_required, no_pending_notes_required
from django.contrib.auth.models import User
from .models import Note, UsedToken, ProfessorRequest
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


# VERIFICARE PAROLA MANUAL
# verificare manuala a parolei in interfata utilizatorului
def password_manual_check_home(user, old_password, new_password1, new_password2):
    if not check_password(old_password, user.password):
        return False, 'Parola veche a fost introdusă greșit!'
    elif new_password1 != new_password2:
        return False, 'Parolele nu se potrivesc!'
    else:
        try:
            validate_password(new_password1, user=user)
            return True, None  # parola indeplineste conditiile
        except ValidationError as e:
            return False, '\n'.join(e.messages)  # parola nu indeplineste conditiile

# verificarea manuala a parolei in pagina principala
def password_manual_check_auth(user, new_password, confirm_password):
    if new_password != confirm_password:
        return False, 'Parolele nu se potrivesc!'

    try:
        validate_password(new_password, user=user)
        return True, None  # parola indeplineste conditiile
    except ValidationError as e:
        return False, '\n'.join(e.messages)  # parola nu indeplineste conditiile

# PAGINA PRINCIPALA
@logout_required()
def main(request):
    page_name = "Pagina principală"
    return render(request, 'unauthenticated/main.html', {'page_name': page_name})


# LOGIN, REGISTER, LOGOUT, RESET PASSWORD
# resetarea parolei dupa apasarea link-ului de verificare, in pagina principala
def reset_password_auth_action(request, uidb64, token):
    page_name = "Resetare parola"
    if request.method == 'POST':
        new_password = request.POST.get('new_password') 
        confirm_password = request.POST.get('confirm_password')

        # decodeaza uid pentru a lua user-ul
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
        
        # verifica daca user-ul a fost luat corect si daca se potriveste token-ul
        if user is not None and reset_password_token.check_token(user, token):
            # verifica manual daca parola e buna si salveaza erorile
            is_valid, error_message = password_manual_check_auth(user, new_password, confirm_password)
            if not is_valid:
                messages.error(request, error_message) # ceva nu a mers bine
            else:
                # salveaza noua parola a user-ului
                user.password = make_password(new_password)
                user.save()

                # marcheaza token-ul ca fiind folosit pentru a face link-ul folosit inaccesibil
                UsedToken.objects.create(user=user, token=token)

                messages.success(request, 'Parola a fost resetată cu succes!')

                # redirectioneaza catre pagina principala
                return redirect('/')

        else:
            messages.error(request, 'Link-ul de resetare nu este valid!')
            return redirect('/')

    # daca sunt erori, incarca pagina iar
    return render(request, 'unauthenticated/reset_password_page.html', {'page_name': page_name, 'uidb64': uidb64, 'token': token})

# redirectionarea catre pagina de resetare a parolei, in pagina principala
def reset_password_auth_page(request, uidb64, token):
    page_name = "Resetare parola"

    # decodeaza uid pentru a lua utilizatorul
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    # verifica daca token-ul a fost folosit deja
    if UsedToken.objects.filter(user=user, token=token).exists():
        messages.error(request, 'Acest link pentru resetare a fost deja folosit! Vă rog să folosiți un link nou.')
        return redirect('/')

    return render(request, 'unauthenticated/reset_password_page.html', {'page_name': page_name, 'uidb64': uidb64, 'token': token})

# crearea si trimiterea email-ului de resetare a parolei in pagina principala
def reset_password_auth(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        # se verifica daca a fost introdus ceva in casuta pentru e-mail
        if not email:
            messages.error(request, 'Trebuie introdus un e-mail!')
            return redirect('/')

        # se verifica daca exista un user asociat e-mail-ului
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Nu există un utilizator cu această adresă de e-mail.')
            return redirect('/')

        # genereaza un token de resetare a parolei
        token_generator = reset_password_token  # se cheama functia custom de creare a token-ului
        uid = urlsafe_base64_encode(force_bytes(user.pk)) # cripteaza utilizatorul
        token = token_generator.make_token(user) # se creeaza un token special pentru utulizator

        # se creeaza corpul e-mail-ului
        mail_subject = 'Resetează parola'
        message = render_to_string('unauthenticated/reset_password_email.html', {
            'user': user,
            'domain': get_current_site(request).domain,
            'uid': uid,
            'token': token,
        })
        email = EmailMessage(mail_subject, message, to=[email])
        email.send()

        # se afiseaza mesajul de succes daca e-mail-ul a fost trimis
        messages.success(request, 'Un e-mail cu un link de schimbare a parolei a fost trimis către adresa de e-mail.')

        return redirect('/')

    return redirect('reset_password_home')

# metoda custom de login
class CustomLoginView(LoginView):
    template_name = 'unauthenticated/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = "Autentificare"  # seteaza numele paginii
        return context

    # se redirectioneaza utilizatorul in functie de grupul in care se afla
    def get_success_url(self):
        user = self.request.user
        
        if user.is_superuser:
            return reverse('home_admin')
        
        if user.groups.filter(name='student').exists():
            # verifica daca studentul are o cerere acceptata
            if Note.objects.filter(author=user, is_accepted=True).exists():
                return reverse('home_student_accepted') 
            else: 
                return reverse('home_student')
        elif user.groups.filter(name='secretar').exists():
            return reverse('home_secretary')
        elif user.groups.filter(name='profesor').exists():
            # se salveaza profesorul cu un flag care spune daca vrea cereri sau nu, asta in cazul in care nu exista deja in tabela
            professor_request, created = ProfessorRequest.objects.get_or_create(professor=user)
            if created:
                professor_request.save()
            return reverse('home_professor')
        else:
            return reverse('main')
        

# deconectare
@login_required(login_url = "/login")
def log_out(request):
    logout(request)
    return redirect("/")

# functia ce reprezinta ca a fost contul activat dupa vizitarea link-ului de activare din e-mail
def activated(request, uidb64, token):
    User = get_user_model() # se ia utilizatorul
    # se decodeaza utilizatorul din uid
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    # verifica daca token-ul a fost folosit deja
    if UsedToken.objects.filter(user=user, token=token).exists():
        messages.error(request, 'Acest link pentru activare a fost deja folosit! Vă rog să folosiți un link nou.')
        return redirect('/')

    # se verifica utilizatorul si token-ul
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True # marcheaza contul ca fiind activ si permite utilizatorului sa il foloseasca
        user.save()

        # marcheaza token-ul ca fiind folosit pentru a face link-ul folosit inaccesibil
        UsedToken.objects.create(user=user, token=token)

        messages.success(request, "Contul ți-a fost activat cu succes! Te poți autentifica.")
    else:
        messages.error(request, "Link-ul de activare nu este valid sau a expirat!")
    return redirect('/main')

# functie de creare a email-ului pentru activarea contului
def activateEmail(request, user, to_email):
    mail_subject = "Activează-ți contul"
    message = render_to_string('unauthenticated/activate_account_email.html', {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })
    email = EmailMessage(mail_subject, message, to = [to_email])
    if email.send():
        messages.success(request, "Link-ul de verificare a fost trimis cu succes!")
    else:
        messages.error(request, "Am întâmpinat o problemă încercând să trimitem link-ul de verificare! Vă rugăm încercați mai târziu.")


# înregistrare
@logout_required()
def sign_up(request):
    page_name = "Înregistrare"
    if request.method == 'POST':
        # se extrag datele introduse de utilizator si se creeaza contul dupa verificare
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # contul se salveaza ca fiind inactiv pana se activeaza prin e-mail
            user.save()
            # se cheama functia ce se ocupa cu e-mail-ul de activare
            activateEmail(request, user, form.cleaned_data.get('email'))
            return redirect('/main')
    else:
        form = RegisterForm()
    return render(request, 'unauthenticated/sign_up.html', {"form": form, "page_name": page_name})

# PAGINI PRINCIPALE
# functie de chenare a paginii unde se face resetarea de parola, in interfata
@login_required(login_url='/login')
def reset_password_home(request):
    return render(request, 'main/reset_password_home.html')

# functie ce se ocupa cu resetarea parolei
@login_required(login_url='/login')
def reset_password_home_action(request):
    if request.method == 'POST':
        # preia datele introduse de utilizator
        user = request.user
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        # cheama functia de verificare manuala
        is_valid, message = password_manual_check_home(user, old_password, new_password1, new_password2)
        
        # verifica daca totul este valid
        if not is_valid:
            messages.error(request, message)
        else:
            # seteaza noua parola a utilizatorului
            user.set_password(new_password1)
            user.save()
            # refresh la pagina
            update_session_auth_hash(request, user)
            messages.success(request, 'Parola ta a fost modificata cu succes!')
            return redirect('/')

    return redirect('reset_password_home')

# interfata studentului
@login_required(login_url='/login')
@group_required('student')
@no_accepted_notes_required
def home_student(request):
    # filtreaza cererile si notificarile pentru a le putea afisa in interfata
    accepted_request = Note.objects.filter(author=request.user, is_accepted=True).exists()
    notifications = Notification.objects.filter(note__author=request.user)
    # verifica daca exista cereri acceptate pentru a stii daca redirectioneaza user-ul catre cealalta interfata a studentului
    if accepted_request:
        return redirect('home_student_accepted')
    else:
        # arata cererile in asteptare
        notes_sent = Note.objects.filter(author=request.user, is_refused=False)
        return render(request, 'main/home_student.html', {'notes_sent': notes_sent, 'notifications': notifications})

# pagina principala a profesorului
@login_required(login_url='/login')
@group_required('profesor')
def home_professor(request):
    professor = request.user
    # filtreaza cererile primite
    notes_received = Note.objects.filter(destination=professor, is_refused=False).select_related('author')
    # verifica daca profesorul este disponibil
    professor_request = ProfessorRequest.objects.get(professor=request.user)
    # butoanele de disponibilitate
    show_remove_button = not professor_request.no_requests
    show_add_button = professor_request.no_requests
    
    if request.method == 'POST':
        form = request.POST
        note_id = request.GET.get('note_id')
        reason = form.get('reason')
        # daca exista o cerere si un motiv
        if note_id and reason:
            try:
                # marcheaza o cerere ca fiind refuzata
                note = get_object_or_404(Note, pk=note_id)
                note.is_refused = True
                note.save()

                # creeaza o notificare pentru student
                Notification.objects.create(note=note, reason=reason)
                
                return HttpResponseRedirect(reverse('home_professor'))
            except Exception as e:
                messages.error(request, "O eroare a apărut în timpul refuzării cererii! Vă rugăm încercați mai târziu.")
                return HttpResponseRedirect(reverse('home_professor'))

    return render(request, "main/home_professor.html", {
        'notes_received': notes_received,
        "show_remove_button": show_remove_button,
        "show_add_button": show_add_button,})

# interfata secretarei
@login_required(login_url='/login')
@group_required('secretar')
def home_secretary(request):
    # cauta departamentul secretariatului ca sa stie ce profesori din ce departament sa arate secretariatului
    secretary_department_group = request.user.groups.exclude(name='secretar').first()
    professors = User.objects.filter(groups__name='profesor').filter(groups=secretary_department_group)
    accepted_notes = Note.objects.filter(destination__in=professors, is_accepted=True) # cererile acceptate

    return render(request, "main/home_secretary.html", {'professors': professors, 'accepted_notes': accepted_notes})

# functie pentru acceptarea cererilor
def accept_note(request, note_id):
    if request.method == 'POST':
        note = get_object_or_404(Note, pk=note_id)
        note.is_accepted = True
        note.save() # salveaza cererea in baza de date ca fiind acceptata

        # ia toate celelalte cereri ale studentului si le pune ca fiind refuzate pentru a se evita acceptarea a doua cereri
        other_notes = Note.objects.filter(author=note.author, is_accepted=False, is_refused=False)
        for other_note in other_notes:
            other_note.is_refused = True
            other_note.save()

    return redirect('home_professor')  # Redirect back to the professor's home page

# CERERI DE LICENTA/DISERATIE
# crearea cererii
@login_required(login_url='/login')
@group_required('student')
def create_note(request):
    # se aleg profesorii din acelasi departament ca si studentul
    user_department_group = request.user.groups.exclude(name='student').first()
    professors = User.objects.filter(groups__name='profesor').exclude(professorrequest__no_requests=True)
    same_dep_professors = [prof for prof in professors if prof.groups.exclude(name='profesor').first() == user_department_group]

    if request.method == 'POST':
        form = NoteForm(request.POST, request=request)
        if form.is_valid():
            professor_id = request.POST.get('destination') # se ia id-ul profesorului care in tabela de cerere este salvat ca fiind destinatia
            if professor_id:
                professor = get_object_or_404(User, id=professor_id)
                author = request.user
                
                # se verifica daca au fost deja trimise 3 cereri catre un profesor, inclusiv cele refuzate
                if Note.objects.filter(author=author, destination=professor).count() >= 1:
                    form_errors = "You have already sent 3 requests to this professor."
                else:
                    # se salveaza cererea
                    note = form.save(commit=False)
                    note.author = author
                    note.destination = professor
                    note.save()
                    return redirect("/home-student")
        else:
            form_errors = "Vă rugăm să vă corectați erorile."
    else:
        form = NoteForm(request=request)
        form_errors = None

    return render(request, 'notes/create_note.html', {"form": form, "professors": same_dep_professors, "form_errors": form_errors})

# pagina de cereri acceptate
@login_required(login_url='/login')
@group_required('student')
@no_pending_notes_required
def home_student_accepted(request):
    # se ia cererea acceptata pentru a se arata pe pagina studentului
    accepted_note = Note.objects.filter(author=request.user, is_accepted=True)
    return render(request, 'notes/accepted.html', {'accepted_notes': accepted_note})

# refuzarea cererilor
@login_required
@group_required('profesor')
def refuse_note(request, note_id):
    if request.method == 'POST':
        # sunt luate id-ul cererii si motivul refuzului
        note_id = request.POST.get('note_id')
        reason = request.POST.get('reason', '')

        if note_id:
            try:
                # marcheaza cererea ca fiind refuzata
                note = Note.objects.get(pk=note_id)
                note.is_refused = True
                note.save()

                # creeaza o notificare pentru student
                Notification.objects.create(note=note, reason=reason)

                messages.success(request, "Cererea a fost respinsă cu succes!")
            except Note.DoesNotExist:
                messages.error(request, "Cererea nu există.")
            except Exception as e:
                messages.error(request, "A apărut o eroare în timpul refuzării cererii! Vă rugăm încercați mai târziu.")
    return HttpResponseRedirect(reverse('home_professor'))

@login_required
@group_required('profesor')
def refuse_all_requests(request):
    # ia toate cererile unde destinatia este id-ul profesorului conectat
    notes_to_refuse = Note.objects.filter(destination=request.user, is_accepted=False, is_refused=False)
    try:
        # marcheaza toate cererile ca fiind refuzate
        notes_to_refuse.update(is_refused=True)
    except Exception as e:
        messages.error(request, f"A apărut o eroare în timpul refuzării tuturor cererilor: {str(e)}")

    return redirect('home_professor')

# ciudat nume pentru o functie, dar face profesorul sa nu mai fie valabil pentru lucrari
@group_required('profesor')
@login_required
def remove_myself(request):
    if request.method == 'POST':
        try:
            # face profesorul sa nu mai fie valabil
            professor_request = ProfessorRequest.objects.get(professor=request.user)
            professor_request.no_requests = True
            professor_request.save()
            messages.success(request, "Nu vei mai primi cereri de licență!")
        except ProfessorRequest.DoesNotExist:
            messages.error(request, "Profesorul nu poate fi găsit.")
    return redirect(reverse('home_professor'))

# la fel de ciudat nume dar face fix opusul functiei de mai sus, adica face profesorul valabil
@group_required('profesor')
@login_required
def add_myself(request):
    if request.method == 'POST':
        try:
            # face profesorul valabil si ii permite să primeasca cereri de licenta
            professor_request = ProfessorRequest.objects.get(professor=request.user)
            professor_request.no_requests = False
            professor_request.save()
            messages.success(request, "Vei primi de acum cereri de licență!")
        except ProfessorRequest.DoesNotExist:
            messages.error(request, "Profesorul nu poate fi găsit.")
    return redirect(reverse('home_professor'))