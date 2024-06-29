from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .decorators import superuser_required
from django.contrib.auth.models import User, Group
from .models import Note, Department, Specialization, ActivityLog

User = get_user_model()

# pentru selectarea user-ului si printarea acestuia in url
@superuser_required
def select_user(request, user_id):
    return redirect('home_admin')

# stegerea tuturor log-urilor
@superuser_required
def delete_all_logs(request):
    ActivityLog.objects.all().delete()
    return redirect('home_admin')

# pagina principala de admin
@superuser_required
def home_admin(request):
    users = User.objects.all()
    notes = Note.objects.all()
    logs = ActivityLog.objects.all()

    # verifica daca au fost introduse ziua si luna pentru log-uri
    if request.method == 'POST':
        selected_user_id = request.POST.get('selected_user')
        day = request.POST.get('day')
        month = request.POST.get('month')
        if day and month:
            day = int(day)
            month = int(month)
            logs = ActivityLog.objects.filter(timestamp__day=day, timestamp__month=month).order_by('-timestamp')

    # ia id-ul user-ului selectat si toate log-urile din baza de date
    elif request.method == 'GET':
        selected_user_id = request.GET.get('selected_user')
        logs = ActivityLog.objects.all()
    
    # ia user-ul, nu numai id-ul
    selected_user = User.objects.filter(id=selected_user_id).first()
    departments = Department.objects.all()
    user_filter = ''
    note_filter = ''

    # cauta user-ul in functie de nume, la fel si la cerere
    if request.method == 'GET':
        user_filter = request.GET.get('user_search_query', '') 
        note_filter = request.GET.get('note_search_query', '')
        action = request.GET.get('action')

        if user_filter:
            users = User.objects.filter(username__icontains=user_filter)

        if note_filter:
            notes = Note.objects.filter(title__icontains=note_filter)

        # verifica ce buton a fost apasat in tab-ul cu toti userii
        if selected_user and action:
            if action == 'delete_users_notes':
                delete_user_and_notes(request, selected_user)
            elif action == 'set_superuser':
                set_superuser(request, selected_user)
            elif action == 'unset_superuser':
                unset_superuser(request, selected_user)
            return redirect('home_admin')
        
    elif request.method == 'POST':
        # daca au fost alese alte optiune pentru grupe, sunt schimbate grupurile utilizatorilor
        action = request.POST.get('action')
        if selected_user and action == 'change_groups_roles':
            change_user_groups(request, selected_user)
            return redirect('home_admin') 
        
    context = {
        'users': users,
        'notes': notes,
        'selected_user': selected_user,
        'user_filter': user_filter,  
        'note_filter': note_filter,
        'departments': departments,
        'activity_logs': logs
    }
    return render(request, 'main/home_admin.html', context)

# schimba grupurile user-ului
@superuser_required
def change_user_groups(request, user):
    group_name = request.POST.get('group')
    department_id = request.POST.get('department')
    
    # sterge toate grupurile pe care le are utilizatorul deja
    user.groups.clear()

    # ia grupul cu rolul (sau le creeaza daca nu exista) si adauga utilizatorul in el
    group, created = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)

    # ia departamentul si adauga utilizatorul in el
    department = Department.objects.get(id=department_id)
    department_group_name = department.name
    department_group, created = Group.objects.get_or_create(name=department_group_name)
    user.groups.add(department_group)
    
    # pentru log-urile din baza de date
    administrator_name = request.user.username
    ActivityLog.objects.create(action = f'Administratorul {administrator_name} a schimbat grupul utilizatorului {user}.')
    messages.success(request, f"Utilizatorul a fost adăugat în {group_name} și {department_group_name}!")
    user.save()

# sterge toate cererile si studentii
@superuser_required
def delete_all_users_notes(request):
    if request.method == 'POST':
        try:
            # sterge toate cererile
            Note.objects.all().delete()
            # sterge toti studentii din grupul "student"
            student_group = Group.objects.get(name='student')
            students = User.objects.filter(groups=student_group)
            students.delete()
            messages.success(request, 'Toți studenții au fost șterși cu success!')

            administrator_name = request.user.username
            ActivityLog.objects.create(action = f'Administratorul {administrator_name} a șters toate cererile și studenții.')

        except Group.DoesNotExist:
            messages.error(request, 'Grupul ”student” nu există.')
        except Exception as e:
            messages.error(request, f'A apărut o eroare: {str(e)}')

    return redirect('home_admin')

# administratorul reseteaza parola unui user (si il face activ in acelasi timp)
@superuser_required
def password_reset_admin(request):
    if request.method == 'POST':
        # ia parola noua prin post
        new_password = request.POST.get('newPassword')
        selected_user_id = request.GET.get('selected_user') or request.POST.get('selected_user')
        selected_user = User.objects.filter(id=selected_user_id).first()

        # daca user-ul e selectat, ii atribuie noua parola si il face activ
        if selected_user:
            selected_user.set_password(new_password)
            selected_user.is_active = True
            selected_user.save()
            messages.success(request, 'Parola a fost salvată cu succes!')

            administrator_name = request.user.username
            ActivityLog.objects.create(action = f'Administratorul {administrator_name} a schimbat parola utilizatorului {selected_user}.')
        else:
            messages.error(request, 'Am întâmpinat o problemă încercând să salvăm parola! Vă rugăm încercați mai târziu.')
        
        return redirect('home_admin')
    
    return redirect('home_admin')

# sterge un user si toate cererile lui
@superuser_required
def delete_user_and_notes(request, selected_user):
    try:
        if selected_user.groups.filter(name='student').exists():
            # ia toate cererile studentului si le sterge
            Note.objects.filter(author=selected_user).delete()
        elif selected_user.groups.filter(name='profesor').exists():
            # ia toate cererile profesorului si le sterge
            Note.objects.filter(destination=selected_user).delete()
        
        # verifica daca utilizatorul e administrator
        if selected_user.is_superuser:
            messages.error(request, f'Nu poți șterge un administrator!')
        else:
            # sterge utilizatorul
            selected_user.delete()
            messages.success(request, f'Utilizatorul {selected_user.username} a fost șters cu succes.')

            administrator_name = request.user.username
            ActivityLog.objects.create(action = f'Administratorul {administrator_name} a șters utilizatorul {selected_user} și cererile sale.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la ștergerea utilizatorului: {str(e)}')

    return redirect('home_admin')

# adauga departament
@superuser_required
def add_department(request):
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        if department_name:
            # creeaza un nou departament folosind input-ul dat de admin
            new_department = Department(name=department_name)
            new_department.save()

            administrator_name = request.user.username
            ActivityLog.objects.create(action = f'Administratorul {administrator_name} a adăugat departamentul {new_department}.')
            return redirect('home_admin')

    return render(request, 'main/home_admin.html')

# adauga specializare pe departament
@superuser_required
def add_specialization(request):
    if request.method == 'POST':
        # sunt luati departamentul, numele noii specializari si numarul de ani
        department_id = request.POST.get('department_id')
        specialization_name = request.POST.get('specialization_name')
        number_of_years = request.POST.get('number_of_years')

        # daca toate exista, se creeaza specializarea in baza de date
        if department_id and specialization_name and number_of_years:
            print("hai sa vedem daca merge")
            department = Department.objects.get(id=department_id)
            Specialization.objects.create(
                department=department,
                name=specialization_name,
                number_of_years=int(number_of_years)
            )
            messages.success(request, 'Specializarea a fost adăugată cu succes!')
            administrator_name = request.user.username
            ActivityLog.objects.create(action = f'Administratorul {administrator_name} a adăugat specializarea {specialization_name} la departamentul {department}.')
            return redirect('home_admin')
        else:
            messages.error(request, "A apărut o eroare! Sunteți rugați să completați toate câmpurile!")

    return render(request, 'main/home_admin.html')

# seteaza un utilizator sa fie administrator
@superuser_required
def set_superuser(request, selected_user):
    try:
        # atribuie rolul de superuser si salveaza
        selected_user.is_superuser = True
        selected_user.save()
        messages.success(request, f'Utilizatorul {selected_user.username} a fost setat ca administrator.')

        administrator_name = request.user.username
        ActivityLog.objects.create(action = f'Administratorul {administrator_name} a dat utilizatorului {selected_user} drepturi de administrator.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la setarea ca administrator: {str(e)}')

    return redirect('home_admin')

# scoate rolul de administrator al unui utilizator
@superuser_required
def unset_superuser(request, selected_user):
    try:
        # scoate rolul de administrator
        selected_user.is_superuser = False
        selected_user.save()
        messages.success(request, f'Utilizatorul {selected_user.username} nu mai este administrator.')
        administrator_name = request.user.username
        ActivityLog.objects.create(action = f'Administratorul {administrator_name} a scos drepturile de administrator ale utilizatorului {selected_user}.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la scoaterea din rolul de administrator: {str(e)}')

    return redirect('home_admin')