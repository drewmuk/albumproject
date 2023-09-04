from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit

from albums import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth

from datetime import datetime, timedelta
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from album_app.forms import UserChoiceForm

from .models import SpotifyToken
import random
from collections import Counter


client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET
redirect_uri = settings.SPOTIFY_REDIRECT_URI_REMOTE

local = 1
if local:
    redirect_uri = settings.SPOTIFY_REDIRECT_URI_LOCAL


scope = "user-library-read, user-top-read"

# read the csv file
try:
    df_all = pd.read_csv('C:/Users/drewm/Desktop/album_project/output.csv', encoding='utf-8')
except:
    df_all = pd.read_csv('/home/dm1202/albumproject/output.csv', encoding='utf-8')

""" df_all_sp = df_all[df_all['Language'] == 'Spanish']
df_all_en = df_all[df_all['Language'] == 'English']

usecols = [2,3,8,9,10,11,12,13,14,15,16]

df_af_values = df_all.iloc[:, usecols]
df_af_values_sp = df_all_sp.iloc[:, usecols]
df_af_values_en = df_all_en.iloc[:, usecols] """

""" af_values_array = df_af_values.values
af_values_array_sp = df_af_values.values
af_values_array_en = df_af_values.values """

# Initialize a new StandardScaler instance


# Fit the scaler to the data and transform the data
""" data_np_scaled = np.round(scaler.fit_transform(af_values_array), 3)
data_np_scaled_sp = np.round(scaler.fit_transform(af_values_array_sp), 3)
data_np_scaled_en = np.round(scaler.fit_transform(af_values_array_en), 3)

scaled_data = data_np_scaled.tolist()
scaled_data_sp = data_np_scaled_sp.tolist()
scaled_data_en = data_np_scaled_en.tolist()

# if you want to convert the dataframe to a list of lists (where each sub-list is a row)
af_values_all = data_np_scaled.tolist()
af_values_all_sp = data_np_scaled_sp.tolist()
af_values_all_en = data_np_scaled_en.tolist()

all_album_data = df_all.values.tolist()
all_album_data_sp = df_all_sp.values.tolist()
all_album_data_en = df_all_en.values.tolist() """

#print(list_temp)
output_titles = ['Artist','Album','Year','Popularity','Duration', 
                      'Cover', 'ID', 'Language','acousticness',
                      'danceability','energy','instrumentalness','loudness',
                      'mode','speechiness','tempo','valence', 'liveness']
language_col = 7

#print(all_album_data)

def get_access_token(client_id, client_secret):
    # Endpoint for getting the access token
    token_url = "https://accounts.spotify.com/api/token"

    # Set the client ID and client secret as the authentication parameters
    auth_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    # Make a POST request to get the access token
    response = requests.post(token_url, data=auth_params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON to get the access token
        access_token = response.json()["access_token"]
        return access_token
    else:
        # Handle the error if the request was unsuccessful
        print("Failed to obtain access token.")
        return None
    
access_token = get_access_token(client_id, client_secret)

headers = {
    "Authorization": f"Bearer {access_token}"
}

def weighted_euclidean(a, b, weights):
    q = a - b
    return np.sqrt((weights*q*q).sum())

# Year, Pop, Acous, Dance, Energy, Instrum, Loud, Mode, Speech, Tempo, Valence
weights = [.1,.2,1,1,1,1,1,0,0,1,0]

def find_similar_items(sample_stats, all_album_stats, top_n=100):
    #data_np = np.array(all_album_stats) # Convert list to numpy array for efficient computation
    item_np = np.array(sample_stats)
    distances = np.array([weighted_euclidean(row, item_np, weights) for row in all_album_stats]) # Euclidean distance
    closest_indices = distances.argsort()[:top_n] # Get indices of top_n closest items
    #closest_items = [all_album_stats[i] for i in closest_indices]
    return closest_indices


# Create your views here.
def home_page(request):
    logged_in = False
    try:
        tokens = SpotifyToken.objects.filter(user=request.user)
    
        if tokens.exists():
            # User is logged in to Spotify
            logged_in = True
        
    
        token_info = tokens[0]
        now = timezone.now()

        if token_info.expires_at < now:
            # Access token has expired
            logged_in = False
        
        return render(request, 'home.html', context = {'logged_in': logged_in})
    except:
        return render(request, 'home.html', context = {'logged_in': logged_in})

@ratelimit(key='ip', rate='5/m')  # Limit of 5 attempts per minute
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            return redirect('spotify_login')
        else:
            # Return an 'invalid login' error message.
            print('here instead')
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
    else:
        return render(request, 'login.html')
    
def user_logout(request):
    print('logged out')
    SpotifyToken.objects.filter(user=request.user).delete()
    cache.clear()
    logout(request)
    return redirect('user_login')
    
def sign_up(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            return render(request, 'sign_up.html', {'error': 'Username already exists.'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('spotify_login')
    else:
        return render(request, 'sign_up.html')

    
def spotify_login(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        scope=scope
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@login_required
def spotify_callback(request):
    code = request.GET.get('code')
    sp = SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                      client_secret=settings.SPOTIFY_CLIENT_SECRET,
                      redirect_uri=redirect_uri,
                      scope=scope)
    
    # Get the authorization code from the URL after the user grants access
    token_info = sp.get_access_token(code)
    expires_at = timezone.now() + timedelta(seconds=token_info['expires_at'])
    
    SpotifyToken.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': token_info['access_token'],
            'refresh_token': token_info['refresh_token'],
            'token_type': token_info['token_type'],
            'expires_at': expires_at
        }
    )

    return redirect('home_page')

def get_access_token(client_id, client_secret):
    # Endpoint for getting the access token
    token_url = "https://accounts.spotify.com/api/token"

    # Set the client ID and client secret as the authentication parameters
    auth_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    # Make a POST request to get the access token
    response = requests.post(token_url, data=auth_params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON to get the access token
        access_token = response.json()["access_token"]
        return access_token
    else:
        # Handle the error if the request was unsuccessful
        print("Failed to obtain access token.")
        return None
    
def refresh_spotify_token(spotify_token, client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    refresh_token = spotify_token.refresh_token

    # Set the client ID and client secret as the authentication parameters
    auth_params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        'refresh_token': refresh_token
    }

    # Make a POST request to get the access token
    response = requests.post(token_url, data=auth_params)

    # Check if the request was successful
    if response.status_code == 200:
        print(response.json())
        # Parse the response JSON to get the access token
        access_token = response.json()["access_token"]
        return access_token
    else:
        # Handle the error if the request was unsuccessful
        print("Failed to obtain access token.")
        return None

def most_common_genres(request):
    spotify_token = SpotifyToken.objects.get()
    
    if spotify_token.expires_at >= timezone.now():
        print('expired')
        new_token = refresh_spotify_token(spotify_token, client_id, client_secret)
    else:
        new_token = spotify_token.access_token

    sp = spotipy.Spotify(auth=new_token)

    limit_tracks = 30
    top_tracks_raw = sp.current_user_top_tracks(limit=limit_tracks)

    genre_list = []
    for track in top_tracks_raw['items']:
        track_artist_id = track['artists'][0]['id']
        artist_url = f"https://api.spotify.com/v1/artists/{track_artist_id}"
        response_artist = requests.get(artist_url, headers=headers)  

        if response_artist.status_code == 200:
            artist_data = response_artist.json()
            artist_genres = artist_data['genres']
        else:
            print("Error", response_artist.status_code)
        
        genre_list.append(artist_genres)


    item_counts = Counter(genre_list)

    # Find the most common items and their counts
    most_common = item_counts.most_common()

    # Print the most common items
    for item, count in most_common:
        print(f"{item}: {count} times")



@login_required
def most_similar_albums(request):
    spotify_token = SpotifyToken.objects.get(user_id=request.user.id)
    language_input = request.GET.get('language_select', 'Both')

    if language_input == 'English':
        df_all_input = df_all[df_all['Language'] == 'English']
    elif language_input == 'Spanish':
        df_all_input = df_all[df_all['Language'] == 'Spanish']
    else:
        df_all_input = df_all

    usecols = [2,3,8,9,10,11,12,13,14,15,16]

    df_af_values = df_all_input.iloc[:, usecols]
    af_values_array = df_af_values.values

    scaler = StandardScaler()

    # Fit the scaler to the data and transform the data
    data_np_scaled = np.round(scaler.fit_transform(af_values_array), 3)
    scaled_data = data_np_scaled.tolist()

    # if you want to convert the dataframe to a list of lists (where each sub-list is a row)
    af_values_all = data_np_scaled.tolist()

    all_album_data = df_all_input.values.tolist()

    if spotify_token.expires_at >= timezone.now():
        print('expired')
        new_token = refresh_spotify_token(spotify_token, client_id, client_secret)
    else:
        new_token = spotify_token.access_token

    sp = spotipy.Spotify(auth=new_token)

    # Get the currently logged in user's top X tracks, cannot be over 50
    limit_tracks = 30
    top_tracks_raw = sp.current_user_top_tracks(limit=limit_tracks)

    print(top_tracks_raw)

    # Get the audio features for these tracks
    all_track_ids = []
    for i in range(0,len(top_tracks_raw['items'])):
        track_id = top_tracks_raw['items'][i]['id']
        all_track_ids.append(track_id)

    query_track_params = {"ids": ",".join(all_track_ids)}
    all_af_url = "https://api.spotify.com/v1/audio-features"
    response_af = requests.get(all_af_url, headers=headers, params=query_track_params)  

    if response_af.status_code == 200:
        all_tracks_data = response_af.json()

        af_values = [0,0,0,0,0,0,0,0,0]
        total_tracks = 0
        for n in range(0,len(all_tracks_data['audio_features'])):
            try:
                ac = all_tracks_data['audio_features'][n]['acousticness']
                da = all_tracks_data['audio_features'][n]['danceability']
                en = all_tracks_data['audio_features'][n]['energy']
                ins = all_tracks_data['audio_features'][n]['instrumentalness']
                lo = all_tracks_data['audio_features'][n]['loudness']
                mo = all_tracks_data['audio_features'][n]['mode']
                sp = all_tracks_data['audio_features'][n]['speechiness']
                te = all_tracks_data['audio_features'][n]['tempo']
                va = all_tracks_data['audio_features'][n]['valence']
                af_values[0] += ac; af_values[1] += da
                af_values[2] += en; af_values[3] += ins
                af_values[4] += lo; af_values[5] += mo 
                af_values[6] += sp; af_values[7] += te
                af_values[8] += va

                total_tracks += 1
            except:
                total_tracks += 0

        # We want the average of the features over all the tracks
        af_values = [x / total_tracks for x in af_values]

    # Need to individually search for each track to get its popularity
    all_tracks_url = "https://api.spotify.com/v1/tracks"
    response_tracks = requests.get(all_tracks_url, headers=headers, params=query_track_params)  

    if response_tracks.status_code == 200:
        all_tracks_data = response_tracks.json()
        #print(all_tracks_data)

        avg_pop = 0
        avg_year = 0
        total_tracks = 0
        for n in range(0,len(all_tracks_data['tracks'])):
            try:
                #print(all_tracks_data['tracks'][n]['album'])
                avg_year += float(all_tracks_data['tracks'][n]['album']['release_date'][:4])
                avg_pop += float(all_tracks_data['tracks'][n]['popularity'])
                total_tracks += 1
            except:
                total_tracks += 0

        # in case genre data ever becomes available
        """     if n < 20:
                track_album = all_tracks_data['tracks'][n]['album']['id']
                track_albums.append(track_album)

        query_track_album_params = {"ids": ",".join(track_albums)}
        all_track_albums_url = "https://api.spotify.com/v1/albums"
        response_track_album = requests.get(all_track_albums_url, headers=headers, params=query_track_album_params)

        genre_list = []

        if response_track_album.status_code == 200:
            all_track_albums_data = response_track_album.json()
            for k in range(0, len(all_track_albums_data['albums'])):
                print(all_track_albums_data['albums'][k])

        else:
            print(response_track_album.status_code) """

        avg_year /= total_tracks
        avg_pop /= total_tracks

    # Adding popularity and reshaping the user's top tracks data
    af_values.insert(0, avg_year)
    af_values.insert(1, avg_pop)
    sample_af_values = np.array(af_values).reshape(1, -1)

    # Start fitting the K-means clusters model based on all the albums
    n_clusters = 100
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
    weighted_data = np.array(scaled_data) * weights # scaled_data has all the available albums
    labels = kmeans.fit_predict(weighted_data) # get the cluster value for each available album 

    # Use the same scaler to transform the sample tracks' data
    scaled_af_values = np.round(scaler.transform(sample_af_values),3)
    list_values = scaled_af_values.tolist()

    # I'm using two different methods to get the most similar albums, then checking which
    # ones are in both. This is the first method: using the K-means clustering.
    cluster_label = kmeans.predict(scaled_af_values)

    same_cluster_indices = [i for i, label in enumerate(labels) if label == cluster_label[0]]
    same_cluster_items = [all_album_data[i] for i in same_cluster_indices]
    
    similar_album_names_cat1 = []
    similar_album_ids_cat1 = []
    for m in range(0,len(same_cluster_indices)):
        similar_album_names_cat1.append(all_album_data[same_cluster_indices[m]][1])
        similar_album_ids_cat1.append(all_album_data[same_cluster_indices[m]][6])

    # This is the second method: using the weighted Euclidian distance between items
    if language_input == 'English':
        distance_closest_indices = find_similar_items(list_values, af_values_all)
    if language_input == 'Spanish':
        distance_closest_indices = find_similar_items(list_values, af_values_all)
    else:
        distance_closest_indices = find_similar_items(list_values, af_values_all)

    similar_album_names_cat2 = []
    similar_album_ids_cat2 = []
    for n in range(0, len(distance_closest_indices)):
        similar_album_names_cat2.append(all_album_data[distance_closest_indices[n]][1])
        similar_album_ids_cat2.append(all_album_data[distance_closest_indices[n]][6])

    # Check which values are in both lists, and append those to the list of similar albums
    all_similar_albums = []
    for p in range(0, len(similar_album_ids_cat1)):
        if similar_album_ids_cat1[p] in similar_album_ids_cat2:
            album_info = []
            album_name = all_album_data[same_cluster_indices[p]][1]
            album_artist = all_album_data[same_cluster_indices[p]][0]
            album_year = all_album_data[same_cluster_indices[p]][2]
            album_pop = all_album_data[same_cluster_indices[p]][3]
            album_length = all_album_data[same_cluster_indices[p]][4]
            album_cover = all_album_data[same_cluster_indices[p]][5]
            album_af = data_np_scaled[same_cluster_indices[p]]
            album_info.append(album_name)
            album_info.append(album_artist)
            album_info.append(album_year)
            album_info.append(album_pop)
            album_info.append(album_length)
            album_info.append(album_cover)
            album_info.append(album_af)
            all_similar_albums.append(album_info)
        
    # Mix up the albums so they're not in alphabetical order by artist
    random.shuffle(all_similar_albums)

    # Process the data and render the template
    context = {'similar_albums': all_similar_albums, 'top_tracks': scaled_af_values, 
               'similar_count': len(all_similar_albums), 'all_count': len(all_album_data)}
    return render(request, 'similar_albums.html', context)


def all_albums(request):
    all_album_data = df_all.values.tolist()

    sort_by1 = request.GET.get('sort_by1', 'Popularity')
    sort_by2 = request.GET.get('sort_by2', 'Random')
    type_sort = request.GET.get('type_sort1', 'desc') == 'desc'
    language_input = request.GET.get('language_select', 'Both')
    
    
    if language_input != 'Both':
        album_table = [dict(zip(output_titles, row)) for row in all_album_data if row[language_col] == language_input] # language_col defined at top
    else:
        album_table = [dict(zip(output_titles, row)) for row in all_album_data]

    if sort_by2 == 'Random':
        try:
            sorted_data = sorted(album_table, key=lambda x: (x[sort_by1].lower(), random.random()), reverse=type_sort)
        except:
            sorted_data = sorted(album_table, key=lambda x: (x[sort_by1], random.random()), reverse=type_sort)
    else:
        try:
            sorted_data = sorted(album_table, key=lambda x: (x[sort_by1].lower(), random.random()), reverse=type_sort)
        except:
            sorted_data = sorted(album_table, key=lambda x: (x[sort_by1], x[sort_by2]), reverse=type_sort)

    context = {'headers': output_titles,
               'rows': sorted_data, 
               'all_count': len(all_album_data)}
    return render(request, 'display_album_table.html', context)

def choose_random(request):
    random_row = df_all.sample()
    print(random_row)
    context = {'album': random_row}
    return render(request, 'random_album.html', context)

""" def form_based_recs(request):
     """

def user_choice_view(request):
    if request.method == 'POST':
        form = UserChoiceForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user's choice to the database
            return redirect('home_page')  # Redirect to a success page or another URL
    else:
        form = UserChoiceForm()
    return render(request, 'user_choice_form.html', {'form': form})

from .forms import AcousticnessForm, DanceabilityForm

def question1_view(request):
    if request.method == 'POST':
        form = AcousticnessForm(request.POST)
        if form.is_valid():
            # Process the form data for Question 1
            selected_options = form.cleaned_data['selected_ac_options']
            # ... Perform further processing ...
    else:
        form = AcousticnessForm()

    return render(request, 'question1_template.html', {'form': form})

def question2_view(request):
    if request.method == 'POST':
        form = DanceabilityForm(request.POST)
        if form.is_valid():
            # Process the form data for Question 1
            selected_options = form.cleaned_data['selected_da_options']
            # ... Perform further processing ...
    else:
        form = DanceabilityForm()

    return render(request, 'question2_template.html', {'form': form})