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

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "description"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        destination_id = self.request.POST.get('destination')
        if destination_id:
            destination = User.objects.get(id=destination_id)
            author = self.request.user
            if Note.objects.filter(author=author, destination=destination).count() >= 5:
                raise forms.ValidationError("You have already sent 5 requests to this professor.")
        return cleaned_data