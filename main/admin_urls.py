from django.urls import path
from . import admin_views  # Import your admin views module

urlpatterns = [
    path('home-admin/', admin_views.home_admin, name = 'home_admin'),
    path('password-reset-admin/', admin_views.password_reset_admin, name='password_reset_admin'),
    path('select-user/<int:user_id>/', admin_views.select_user, name='select_user'),
]
