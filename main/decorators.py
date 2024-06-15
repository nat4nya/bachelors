from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps
from .models import Note  # Import your Note model here

def group_required(group_name):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Nu ai permisiunea de a accesa acesta pagina!")
        return _wrapped_view
    return decorator

def logout_required(redirect_url=None):
    def decorator(view_function):
        @wraps(view_function)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.groups.filter(name='student').exists():
                    return redirect('/home-student')
                elif request.user.groups.filter(name='professor').exists():
                    return redirect('/home-professor')
                elif request.user.groups.filter(name='secretary').exists():
                    return redirect('/home-secretary')  
            return view_function(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def no_accepted_notes_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the user has any accepted notes
        if Note.objects.filter(author=request.user, is_accepted=True).exists():
            return HttpResponseForbidden("You are not allowed to access this page.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def no_pending_notes_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get all notes for the user
        user_notes = Note.objects.filter(author=request.user)
        # Loop through the notes to check if any is accepted
        is_pending = True
        for note in user_notes:
            if note.is_accepted:
                is_pending = False
                break
                
        if is_pending:
            return HttpResponseForbidden("You are not allowed to access this page.")
        # If no accepted notes are found, proceed to the original view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view