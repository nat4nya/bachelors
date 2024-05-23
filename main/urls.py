from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('main', views.main, name='main'),
    path('home', views.home, name = 'home'),
    path('home-student', views.home_student, name = "home_student"),
    path("home-professor", views.home_professor, name = "home_professor"),
    path('home-secretary', views.home_secretary, name = "home_secretary"),
    path('sign-up', views.sign_up, name='sign_up'),
    path("logout/", views.log_out, name="logout"),
    path("create-post", views.create_post, name = "create_post")
]
