from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    path('', views.main, name='main'),
    path('main', views.main, name='main'),
    path('home-student', views.home_student, name = "home_student"),
    path("home-professor", views.home_professor, name = "home_professor"),
    path('accept-note/<int:note_id>/', views.accept_note, name='accept_note'),
    path('home-professor/refuse-note/<int:note_id>/', views.refuse_note, name='refuse_note'),  # Updated URL pattern
    path('home-secretary', views.home_secretary, name = "home_secretary"),
    path('sign-up', views.sign_up, name='sign_up'),
    path("logout/", views.log_out, name="logout"),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('create-note/', views.create_note, name='create_note'),
    path("home-student/accepted/", views.home_student_accepted, name="home_student_accepted"),
]
