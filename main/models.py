from django.db import models
from django.contrib.auth.models import User

class Note(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notes')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False) 

    def __str__(self):
        return f"Cerere de la {self.author} adresata lui {self.destination}: {self.title}"