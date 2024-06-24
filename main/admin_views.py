from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from .decorators import superuser_required
from django.contrib.auth.models import User, Group
from .models import Note, Department, Specialization

User = get_user_model()

def select_user(request, user_id):
    # Handle the selection of a user
    # For example, redirect or set session variable
    return redirect('home_admin')

@superuser_required
def home_admin(request):
    users = User.objects.all()
    notes = Note.objects.all()
    selected_user_id = request.GET.get('selected_user')
    selected_user = User.objects.filter(id=selected_user_id).first()
    departments = Department.objects.all()
    user_filter = ''
    note_filter = ''

    if request.method == 'GET':
        user_filter = request.GET.get('user_search_query', '')  # Ensure to retrieve search_query parameter
        note_filter = request.GET.get('note_search_query', '')  # Ensure to retrieve note_search_query parameter

        if user_filter:
            users = User.objects.filter(username__icontains=user_filter)

        if note_filter:
            notes = Note.objects.filter(title__icontains=note_filter)  # Adjust this based on your Note model fields

        action = request.GET.get('action')
        if selected_user and action:
            if action == 'delete_users_notes':
                delete_user_and_notes(request, selected_user)
            elif action == 'change_groups_roles':
                # Perform action 3 for selected_user
                pass
            elif action == 'set_superuser':
                set_superuser(request, selected_user)
            elif action == 'unset_superuser':
                unset_superuser(request, selected_user)
            return redirect('home_admin')

    context = {
        'users': users,
        'notes': notes,
        'selected_user': selected_user,
        'user_filter': user_filter,  # Ensure search_query is added to the context
        'note_filter': note_filter,  # Ensure note_filter is added to the context
        'departments': departments
    }
    return render(request, 'main/home_admin.html', context)

# in curs de verificare
def delete_all_users_notes(request):
    if request.method == 'POST':
        try:
            # Delete all notes
            Note.objects.all().delete()
            messages.success(request, 'All notes deleted successfully.')
            # Delete all users in the "student" group
            student_group = Group.objects.get(name='student')  # Adjust group name as per your setup
            students = User.objects.filter(groups=student_group)
            students.delete()
            messages.success(request, 'All students deleted successfully.')

        except Group.DoesNotExist:
            messages.error(request, 'The "student" group does not exist.')
        except Exception as e:
            messages.error(request, f'Error deleting data: {str(e)}')

    return redirect('home_admin')  # Redirect to home_admin or any desired page after deletion

def password_reset_admin(request):
    if request.method == 'POST':
        new_password = request.POST.get('newPassword')
        selected_user_id = request.GET.get('selected_user') or request.POST.get('selected_user')
        selected_user = User.objects.filter(id=selected_user_id).first()

        if selected_user:
            selected_user.set_password(new_password)
            selected_user.is_active = True
            selected_user.save()
            messages.success(request, 'Parola a fost salvată cu succes!')
        else:
            messages.error(request, 'Am întâmpinat o problemă încercând să salvăm parola! Vă rugăm încercați mai târziu.')
        
        return redirect('home_admin')  # Always redirect after processing POST request
    
    # Handle GET request or any other case
    return redirect('home_admin')

def delete_user_and_notes(request, selected_user):
    try:
        if selected_user.groups.filter(name='student').exists():
            # Delete all notes where the selected user is the author (student)
            Note.objects.filter(author=selected_user).delete()
        elif selected_user.groups.filter(name='profesor').exists():
            # Delete all notes where the selected user is the destination (professor)
            Note.objects.filter(destination=selected_user).delete()
        elif selected_user.groups.filter(name='secretar').exists():
            pass
        
        # Check if the selected user is a superuser
        if selected_user.is_superuser:
            messages.error(request, f'Nu poți șterge un administrator!')
        else:
            # Now, delete the selected user
            selected_user.delete()
            messages.success(request, f'Utilizatorul {selected_user.username} a fost șters cu succes.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la ștergerea utilizatorului: {str(e)}')

    return redirect('home_admin')











def add_department(request):
    if request.method == 'POST':
        department_name = request.POST.get('department_name')
        if department_name:
            # Create and save the new department
            new_department = Department(name=department_name)
            new_department.save()
            # Optionally, you can add success messages or perform other actions
            return redirect('home_admin')  # Redirect to a relevant page after adding

    return render(request, 'main/home_admin.html')  # Replace 'your_template.html' with your actual template

def add_specialization(request):
    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        specialization_name = request.POST.get('specialization_name')
        number_of_years = request.POST.get('number_of_years')

        if department_id and specialization_name and number_of_years:
            print("hai sa vedem daca merge")
            department = Department.objects.get(id=department_id)
            Specialization.objects.create(
                department=department,
                name=specialization_name,
                number_of_years=int(number_of_years)
            )
            messages.success(request, 'Specializarea a fost adăugată cu succes!')
            return redirect('home_admin')  # Redirect to a relevant page after adding
        else:
            messages.error(request, "A apărut o eroare! Sunteți rugați să completați toate câmpurile!")

    return render(request, 'main/home_admin.html')










def set_superuser(request, selected_user):
    try:
        selected_user.is_superuser = True
        selected_user.save()
        messages.success(request, f'Utilizatorul {selected_user.username} a fost setat ca administrator.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la setarea ca administrator: {str(e)}')

    return redirect('home_admin')

def unset_superuser(request, selected_user):
    try:
        selected_user.is_superuser = False
        selected_user.save()
        messages.success(request, f'Utilizatorul {selected_user.username} nu mai este administrator.')
    except Exception as e:
        messages.error(request, f'A apărut o problemă la scoaterea din rolul de administrator: {str(e)}')

    return redirect('home_admin')