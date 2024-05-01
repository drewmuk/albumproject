from django.db import models
from django import forms
from django.contrib.auth.models import User, UserManager
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


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


class Input_Artist(models.Model):
    name = models.CharField(max_length=255)
    artist_id = models.CharField(max_length=255)
    language = models.CharField(max_length=255, db_index=True)
    done = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
class Song(models.Model):
    name = models.CharField(max_length=255)
    primary_artist = models.CharField(max_length=255)
    artists = models.ManyToManyField(Artist, related_name='song_artists')
    duration_min = models.IntegerField()
    duration_sec = models.IntegerField()
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

    """completed_lists = models.ManyToManyField(CompletedList, related_name='album_completed_lists')
    to_do_lists = models.ManyToManyField(ToDoList, related_name = 'album_to_do_lists')"""

    def __str__(self):
        return self.name

class Input_Album(models.Model):
    name = models.CharField(max_length=255)
    album_id = models.CharField(max_length=255)
    done = models.IntegerField(default=0)


    def __str__(self):
        return self.name

class Omit_Album(models.Model):
    name = models.CharField(max_length=255)
    album_id = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Last_Update(models.Model):
    date_id = models.IntegerField(default=1)
    update_date = models.DateField(null=True, blank=True)

class CompletedList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    albums = models.ManyToManyField(Album, related_name='completed_list_albums')

class ToDoList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    albums = models.ManyToManyField(Album, related_name='to_do_list_albums')
""" 
class CustomUser(models.Model):
    completed_list = models.OneToOneField(CompletedList, on_delete=models.CASCADE, related_name='user_comp_list')
    to_do_list = models.OneToOneField(ToDoList, on_delete=models.CASCADE, related_name='user_to_do_list')

    REQUIRED_FIELDS = [] """
    
    
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