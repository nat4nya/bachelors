from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps
from .models import Note

# restrictii pentru anumite functii din views.py
# numai un anume grup are voie sa acceseze ceva
def group_required(group_name):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Nu ai permisiunea de a accesa acesta pagina!")
        return _wrapped_view
    return decorator

# site-ul poate fi accesat numai daca utilizatorul nu este autentificat
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

# site-ul poate fi vizitat numai daca studentul nu are cereri acceptate
def no_accepted_notes_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if Note.objects.filter(author=request.user, is_accepted=True).exists():
            return HttpResponseForbidden("Nu ai permisiunea de a accesa acesta pagina!")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# site-ul poate fi vizitat numai daca studentul nu are cereri in asteptare
def no_pending_notes_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_notes = Note.objects.filter(author=request.user)
        is_pending = True
        for note in user_notes:
            if note.is_accepted:
                is_pending = False
                break
        if is_pending:
            return HttpResponseForbidden("Nu ai permisiunea de a accesa acesta pagina!")
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# numai adminii au voie aici
def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("Nu ai permisiunea de a accesa această pagină!")
    return _wrapped_view