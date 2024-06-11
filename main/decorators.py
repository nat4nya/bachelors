from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps

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