from django.urls import path
from . import admin_views  # Import your admin views module

urlpatterns = [
    path('home-admin/', admin_views.home_admin, name = 'home_admin'),
    path('password-reset-admin/', admin_views.password_reset_admin, name='password_reset_admin'),
    path('select-user/<int:user_id>/', admin_views.select_user, name='select_user'),
    path('set-superuser/', admin_views.set_superuser, name='set_superuser'),
    path('unset-superuser/', admin_views.unset_superuser, name='unset_superuser'),
    path('delete-all-users-notes/', admin_views.delete_all_users_notes, name='delete_all_users_notes'),
    path('add_department/', admin_views.add_department, name='add_department'),
    path('add_specialization/', admin_views.add_specialization, name='add_specialization'),
    path('logs/', admin_views.view_logs, name='view_logs'),
    path('delete-all-logs/', admin_views.delete_all_logs, name='delete_all_logs'),
]
