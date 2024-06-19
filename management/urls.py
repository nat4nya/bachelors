from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # asta trebuie bagat aici ca sa ia url-urile din folder-ul aplicatiei nu de aici
    path('', include('main.urls')),
    path('', include('main.admin_urls')),
    path('', include('django.contrib.auth.urls')),
]
