from django.shortcuts import render, redirect
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

from .models import SpotifyToken, Album, Genre, Artist, Song
import random
import urllib.parse

from .forms import YearFilterForm

client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET
redirect_uri = settings.SPOTIFY_REDIRECT_URI_REMOTE
scope = "user-library-read user-top-read user-library-modify"

local = 0
""" # read the csv file
try:
    df_all = pd.read_csv('C:/Users/drewm/Desktop/album_project/input_output/output.csv', encoding='utf-8')
    local = 1
except:
    df_all = pd.read_csv('/home/dm1202/albumproject/input_output/output.csv', encoding='utf-8') """

df_all = pd.DataFrame(list(Album.objects.all().values()))
all_album_data = df_all.values.tolist()
#df_all = pd.DataFrame(list_df_all)
#list_raw_albums = list(raw_all_albums)

if local:
    redirect_uri = settings.SPOTIFY_REDIRECT_URI_LOCAL

#print(list_temp)
output_titles = ['ID','Artist','Album','Year','Popularity','Duration', 
                      'Cover', 'ID', 'Language','acousticness',
                      'danceability','energy','instrumentalness','loudness',
                      'mode','speechiness','tempo','valence', 'liveness',
                      'genres']
year_col = 3
pop_col = 4
id_col = 7
language_col = 8

# Year, Pop, Acous, Dance, Energy, Instrum, Loud, Mode, Speech, Tempo, Valence
weights = [.1,.2,1,1,1,1,1,0,0,1,0]

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
    
def weighted_euclidean(a, b, weights):
    q = a - b
    return np.sqrt((weights*q*q).sum())

def find_similar_items(sample_stats, all_album_stats, top_n=100):
    #data_np = np.array(all_album_stats) # Convert list to numpy array for efficient computation
    item_np = np.array(sample_stats)
    distances = np.array([weighted_euclidean(row, item_np, weights) for row in all_album_stats]) # Euclidean distance
    closest_indices = distances.argsort()[:top_n] # Get indices of top_n closest items
    #closest_items = [all_album_stats[i] for i in closest_indices]
    return closest_indices

def get_genres(top_tracks):
    # Get a list of all unique genres in a set of tracks

    genre_list = []
    for track in top_tracks['items']:
        track_artist_id = track['artists'][0]['id']
        artist_url = f"https://api.spotify.com/v1/artists/{track_artist_id}"
        response_artist = requests.get(artist_url, headers=headers)  

        if response_artist.status_code == 200:
            artist_data = response_artist.json()
            for genre in artist_data['genres']:
                genre_list.append(genre)
        else:
            print("Error", response_artist.status_code)

    unique_temp = set(genre_list)
    all_genres = list(unique_temp)

    return all_genres

@login_required
def most_similar_albums(request):
    language_input = request.GET.get('language_select', 'Both')

    """ This could be more efficient,
    but right now it's filtering based on language and pulling the
    data from the scraped album database """

    if language_input != 'Both':
        album_queryset = Album.objects.filter(language=language_input)
        selected_data = Album.objects.values('year', 'pop', 'acousticness',
                                         'danceability', 'energy', 'instrumentalness',
                                         'loudness', 'mode', 'speechiness', 
                                         'tempo', 'valence').filter(language=language_input)
    else:
        album_queryset = Album.objects.all()
        selected_data = Album.objects.values('year', 'pop', 'acousticness',
                                         'danceability', 'energy', 'instrumentalness',
                                         'loudness', 'mode', 'speechiness', 
                                         'tempo', 'valence')
    
    df_all_input = pd.DataFrame(list(album_queryset.values()))
    
    data_list = list(selected_data)
    df_af_values = pd.DataFrame(data_list)
    af_values_array = df_af_values.values

    scaler = StandardScaler()

    # Fit the scaler to the data and transform the data
    data_np_scaled = np.round(scaler.fit_transform(af_values_array), 3)
    scaled_data = data_np_scaled.tolist()

    all_album_data = df_all_input.values.tolist()

    spotify_token = SpotifyToken.objects.get(user_id=request.user.id)

    if spotify_token.expires_at >= timezone.now():
        new_token = refresh_spotify_token(spotify_token, client_id, client_secret)
    else:
        new_token = spotify_token.access_token

    sp = spotipy.Spotify(auth=new_token)

    # Get the currently logged in user's top X tracks, cannot be over 50
    limit_tracks = 30
    top_tracks_raw = sp.current_user_top_tracks(limit=limit_tracks)

    #print(top_tracks_raw)

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
    else:
        print(response_af.status_code)

    # Need to individually search for each track to get its popularity
    all_tracks_url = "https://api.spotify.com/v1/tracks"
    response_tracks = requests.get(all_tracks_url, headers=headers, params=query_track_params)  

    if response_tracks.status_code == 200:
        all_tracks_data = response_tracks.json()

        avg_pop = 0
        avg_year = 0
        total_tracks = 0
        for n in range(0,len(all_tracks_data['tracks'])):
            try:
                avg_year += float(all_tracks_data['tracks'][n]['album']['release_date'][:4])
                avg_pop += float(all_tracks_data['tracks'][n]['popularity'])
                total_tracks += 1
            except:
                total_tracks += 0

        # in case album by album genre data ever becomes available
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
    
    similar_album_names_cat1 = []
    similar_album_ids_cat1 = []
    for m in range(0,len(same_cluster_indices)):
        similar_album_names_cat1.append(all_album_data[same_cluster_indices[m]][1])
        similar_album_ids_cat1.append(all_album_data[same_cluster_indices[m]][6])

    # This is the second method: using the weighted Euclidian distance between items
    if language_input == 'English':
        distance_closest_indices = find_similar_items(list_values, scaled_data)
    if language_input == 'Spanish':
        distance_closest_indices = find_similar_items(list_values, scaled_data)
    else:
        distance_closest_indices = find_similar_items(list_values, scaled_data)

    similar_album_names_cat2 = []
    similar_album_ids_cat2 = []
    for n in range(0, len(distance_closest_indices)):
        similar_album_names_cat2.append(all_album_data[distance_closest_indices[n]][1])
        similar_album_ids_cat2.append(all_album_data[distance_closest_indices[n]][id_col])

    # Check which values are in both lists, and append those to the list of similar albums
    sim_albums_temp = []
    for p in range(0, len(similar_album_ids_cat1)):
        if similar_album_ids_cat1[p] in similar_album_ids_cat2:
            album_info = []
            album_id = all_album_data[same_cluster_indices[p]][id_col]

            # Get the relevant information about the albums (artists & genres)
            album_instance = Album.objects.get(album_id=album_id)
            album_artist = album_instance.artists.first().name
            
            associated_genres = album_instance.genres.all()
            album_genres = [genre.name for genre in associated_genres]

            album_name = all_album_data[same_cluster_indices[p]][1]
            album_year = all_album_data[same_cluster_indices[p]][year_col]
            album_pop = all_album_data[same_cluster_indices[p]][pop_col]
            album_length = all_album_data[same_cluster_indices[p]][4]
            album_cover = all_album_data[same_cluster_indices[p]][5]

            album_af = data_np_scaled[same_cluster_indices[p]]

            album_info.append(album_name)
            album_info.append(album_artist)
            album_info.append(album_year)
            album_info.append(album_pop)
            album_info.append(album_length)
            album_info.append(album_cover)
            album_info.append(album_id)
            album_info.append(album_af)
            album_info.append(album_genres)
            sim_albums_temp.append(album_info)

    all_similar_albums = []

    top_genres = get_genres(top_tracks_raw)

    # Check which of the most similar albums also match any of the genres
    # from the user's top tracks
    for sim_album in sim_albums_temp:
        album_genres = sim_album[8]
        for genre in album_genres:
            # String formatting
            cleaned_genre = genre.replace("'", '').replace('[', '').replace(']', '')
            if cleaned_genre in top_genres:
                all_similar_albums.append(sim_album)

    # Mix up the albums so they're not in alphabetical order by artist
    random.shuffle(all_similar_albums)

    # Process the data and render the template
    context = {'similar_albums': all_similar_albums, 'top_tracks': scaled_af_values, 
               'similar_count': len(all_similar_albums), 'all_count': len(all_album_data)}
    
    return render(request, 'similar_albums.html', context)

def add_to_lib(request):
    spotify_token = SpotifyToken.objects.get(user_id=request.user.id)

    if spotify_token.expires_at >= timezone.now():
        print('expired')
        new_token = refresh_spotify_token(spotify_token, client_id, client_secret)
    else:
        new_token = spotify_token.access_token

    sp = spotipy.Spotify(auth=new_token)

    album_id = request.GET.get('album_id', '')
    album_name = urllib.parse.unquote(request.GET.get('album_name', ''))
    artist_name = urllib.parse.unquote(request.GET.get('artist_name', ''))

    if album_id:
        """ already_saved = False
        if sp.current_user_saved_albums_contains(albums=[album_id]):
            already_saved = True """
        # Save the album to your library
        sp.current_user_saved_albums_add([album_id])
        context = {'album_name': album_name,
                    'artist_name': artist_name,
                    'album_id': album_id}
            
        return render(request, 'save_success.html', context)
    
def rem_from_lib(request):
    spotify_token = SpotifyToken.objects.get(user_id=request.user.id)

    if spotify_token.expires_at >= timezone.now():
        print('expired')
        new_token = refresh_spotify_token(spotify_token, client_id, client_secret)
    else:
        new_token = spotify_token.access_token

    sp = spotipy.Spotify(auth=new_token)

    album_id = request.GET.get('album_id', '')
    album_name = urllib.parse.unquote(request.GET.get('album_name', ''))
    artist_name = urllib.parse.unquote(request.GET.get('artist_name', ''))

    if album_id:
        # Remove the album from your library
        sp.current_user_saved_albums_delete([album_id])
        context = {'album_name': album_name,
                    'artist_name': artist_name,
                    'album_id': album_id}
            
        return render(request, 'delete_success.html', context)

def all_albums(request):
    # Get the input values from the web page forms
    sort_by1 = request.GET.get('sort_by1', 'Popularity')
    sort_by2 = request.GET.get('sort_by2', 'Random')
    type_sort = request.GET.get('type_sort1', 'desc') == 'desc'
    language_input = request.GET.get('language_select', 'Both')
    pop_input = request.GET.get('pop_select')
    form = YearFilterForm(request.GET)

    if form.is_valid():
        min_year = form.cleaned_data['min_year']
        max_year = form.cleaned_data['max_year']
    else:
        print('invalid form')
    
    # Formatting the parameters & title for year filtering
    if min_year == None and max_year == None:
        mtitle = ''
        min_year = 0
        max_year = 3000
    elif min_year == None:
        mtitle = ' pre-' + str(max_year)
        min_year = 0
    elif max_year == None:
        mtitle = ' post-' + str(min_year)
        max_year = 3000
    else:
        mtitle = ' between ' + str(min_year) + ' and ' + str(max_year)

    # Formatting the parameters & title for popularity filtering
    if pop_input == 'High':
        ptitle = 'High Popularity'
        min_pop = 75
        max_pop = 100
    elif pop_input == 'Medium':
        ptitle = 'Medium Popularity'
        min_pop = 50
        max_pop = 75
    elif pop_input == 'Low':
        ptitle = 'Low Popularity'
        min_pop = 0
        max_pop = 50
    else:
        ptitle = ''
        min_pop = 0
        max_pop = 100

    # Formatting the parameters & title for language filtering
    if language_input != 'Both':
        ltitle = language_input
        album_table = [
            dict(zip(output_titles, row)) 
            for row in all_album_data 
            if row[language_col] == language_input
            and int(row[year_col]) >= min_year
            and int(row[year_col]) < max_year
            and int(row[pop_col]) > min_pop
            and int(row[pop_col]) <= max_pop
        ] 
        # id_col, language_col, year_col, pop_col defined at top
    else:
        ltitle = ''
        album_table = [
            dict(zip(output_titles, row)) 
            for row in all_album_data 
            if int(row[year_col]) >= min_year
            and int(row[year_col]) < max_year
            and int(row[pop_col]) > min_pop
            and int(row[pop_col]) <= max_pop
        ]

    title = 'All ' + ltitle + ' ' + ptitle + ' Albums in Database ' + mtitle

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
               'title': title,
               'cat_count': len(album_table),
               'all_count': len(all_album_data),
               'form': form}
    
    return render(request, 'display_album_table.html', context)

def choose_random(request):
    random_row = df_all.sample().values.tolist()[0]
    print(random_row)
    context = {'album': random_row, 
               'all_count': len(df_all)}
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