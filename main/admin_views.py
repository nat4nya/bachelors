from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .decorators import superuser_required

User = get_user_model()

def select_user(request, user_id):
    # Handle the selection of a user
    # For example, redirect or set session variable
    return redirect('home_admin')

@superuser_required
def home_admin(request):
    users = User.objects.all()
    selected_user_id = request.GET.get('selected_user')
    selected_user = User.objects.filter(id=selected_user_id).first()

    if request.method == 'GET':
        search_query = request.GET.get('search_query', '')  # Ensure to retrieve search_query parameter
        if search_query:
            users = User.objects.filter(username__icontains=search_query)

        action = request.GET.get('action')
        if selected_user and action:
            # Perform actions based on action value
            if action == 'action1':
                # Perform action 1 for selected_user
                pass
            elif action == 'action2':
                # Perform action 2 for selected_user
                pass
            elif action == 'action3':
                # Perform action 3 for selected_user
                pass
            elif action == 'action4':
                # Perform action 4 for selected_user
                pass
            return redirect('home_admin')

    context = {
        'users': users,
        'selected_user': selected_user,
        'user_filter': search_query,  # Ensure search_query is added to the context
    }
    return render(request, 'main/home_admin.html', context)


def password_reset_admin(request):
    if request.method == 'POST':
        new_password = request.POST.get('newPassword')
        selected_user_id = request.GET.get('selected_user') or request.POST.get('selected_user')
        selected_user = User.objects.filter(id=selected_user_id).first()

        print("Selected_user:")
        print(selected_user)
        print("Selected_user_id:")
        print(selected_user_id)

        if selected_user:
            selected_user.set_password(new_password)
            selected_user.save()
            messages.success(request, 'Parola a fost salvată cu succes!')
        else:
            messages.error(request, 'Am întâmpinat o problemă încercând să salvăm parola! Vă rugăm încercați mai târziu.')
        
        return redirect('home_admin')  # Always redirect after processing POST request
    
    # Handle GET request or any other case
    return redirect('home_admin')
