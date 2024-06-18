from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.main, name='main'),
    path('main/', views.main, name='main'),\
    path('home-student/', views.home_student, name='home_student'),
    path('home-professor/', views.home_professor, name='home_professor'),
    path('home-admin/', views.home_admin, name = 'home_admin'),
    path('accept-note/<int:note_id>/', views.accept_note, name='accept_note'),
    path('home-professor/refuse-note/<int:note_id>/', views.refuse_note, name='refuse_note'),  # Updated URL pattern
    path('remove-myself/', views.remove_myself, name='remove_myself'),
    path('add-myself/', views.add_myself, name='add_myself'),
    path('home-secretary/', views.home_secretary, name='home_secretary'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path("logout/", views.log_out, name="logout"),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('create-note/', views.create_note, name='create_note'),
    path('home-student/accepted/', views.home_student_accepted, name='home_student_accepted'),
    path('refuse-all/', views.refuse_all_requests, name='refuse_all_requests'),
    path('activated/<uidb64>/<token>/', views.activated, name='activated'),  # Note the trailing slash here
    path('reset-password-home/', views.reset_password_home, name='reset_password_home'),
    path('reset-password/action/', views.reset_password_home_action, name='reset_password_home_action'),
    path('reset-password-auth/', views.reset_password_auth, name='reset_password_auth'),
    path('reset-password-auth-page/<uidb64>/<token>/', views.reset_password_auth_page, name='reset_password_auth_page'),
    path('reset-password-auth-action/<uidb64>/<token>/', views.reset_password_auth_action, name='reset_password_auth_action'),
]
