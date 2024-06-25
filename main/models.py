from django.db import models
from django.contrib.auth.models import User

# tabelele din baza de date
# modelul cererii
class Note(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notes')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1500)
    created_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    is_refused = models.BooleanField(default=False)

    def __str__(self):
        return f"Cerere de la {self.author} adresata lui {self.destination}: {self.title}"

# modelul notificarii ce va aparea in interfata studentului
class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    note = models.ForeignKey('Note', on_delete=models.CASCADE)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.note.author.username} regarding '{self.note.title}'"

# modelul ce tine cont daca un profesor primeste cereri sau nu
class ProfessorRequest(models.Model):
    professor = models.OneToOneField(User, on_delete=models.CASCADE)
    no_requests = models.BooleanField(default=False)

    def __str__(self):
        return self.professor.username

# modelul de tine cont daca un e-mail de resetare a parolei a fost folosit sau nu
class UsedToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

# modelul departamentului
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
# modelul specializarii
class Specialization(models.Model):
    specialization_id = models.AutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    number_of_years = models.PositiveIntegerField()

    def __str__(self):
        return self.name
    
# pentru istoric in pagina de admin
class ActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=500)

    def __str__(self):
        return f'{self.timestamp} - {self.action}'