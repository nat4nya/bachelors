from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('main', views.main, name='main'),
    path('home', views.home, name = 'home'),
    path('sign-up', views.sign_up, name='sign_up'),
    path("logout/", views.log_out, name="logout"),
]
