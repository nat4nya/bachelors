from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Note(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notes')
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_refused = models.BooleanField(default=False)  # New field for refused notes

    def __str__(self):
        return f"Cerere de la {self.author} adresata lui {self.destination}: {self.title}"

class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    note = models.ForeignKey('Note', on_delete=models.CASCADE)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.note.author.username} regarding '{self.note.title}'"


