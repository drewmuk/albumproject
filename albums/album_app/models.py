from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your models here.
class SpotifyToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=50)
    expires_in = models.DateTimeField()
    last_refreshed = models.DateTimeField(auto_now = True)

class UserChoice(models.Model):
    CHOICES = (
        ('Option1', 'Option 1'),
        ('Option2', 'Option 2'),
    )
    choice = models.CharField(max_length=10, choices=CHOICES)

class MultipleOptionsForm(forms.Form):
    OPTIONS = (
        ('option1', 'Option 1'),
        ('option2', 'Option 2'),
        ('option3', 'Option 3'),
        ('option4', 'Option 4'),
        ('option5', 'Option 5'),
    )
    
    selected_options = forms.MultipleChoiceField(
        choices=OPTIONS,
        widget=forms.CheckboxSelectMultiple,
    )