from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# Create your models here.
class SpotifyToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)
    token_type = models.CharField(max_length=50)
    expires_at = models.DateTimeField()
    last_refreshed = models.DateTimeField(auto_now = True)

class Artist(models.Model):
    name = models.CharField(max_length=255)
    artist_id = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Song(models.Model):
    name = models.CharField(max_length=255)
    artists = models.ManyToManyField(Artist, related_name='song_artists')
    duration_min = models.FloatField()
    duration_sec = models.FloatField()
    number = models.IntegerField()
    song_id = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Genre(models.Model):
    name = models.CharField(max_length=255)
    #genre_id = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name

class Album(models.Model):
    artists = models.ManyToManyField(Artist, related_name='album_artists')
    primary_artist = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    year = models.IntegerField()
    pop = models.IntegerField()
    duration = models.FloatField()
    cover = models.CharField(max_length=255)
    album_id = models.CharField(max_length=255)
    language = models.CharField(max_length=255)
    acousticness = models.FloatField()
    danceability = models.FloatField()
    energy = models.FloatField()
    instrumentalness = models.FloatField()
    loudness = models.FloatField()
    mode = models.FloatField()
    speechiness = models.FloatField()
    tempo = models.FloatField()
    valence = models.FloatField()
    liveness = models.FloatField()
    genres = models.ManyToManyField(Genre, related_name='album_genre')
    songs = models.ManyToManyField(Song, related_name='albums_songs')

    def __str__(self):
        return self.name

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