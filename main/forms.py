from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import ValidationError
from .models import Note

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@uab.ro'):
            raise ValidationError("Only email addresses ending with '@uab.ro' are allowed.")
        return email

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "description"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)