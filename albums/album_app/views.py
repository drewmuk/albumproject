from django.shortcuts import render, redirect
from django.http import HttpResponse
from albums import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import csv
import requests
import numpy as np
from scipy.spatial import distance
import pandas as pd
from sklearn.preprocessing import StandardScaler

client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET

means = []
std_devs = []

""" def standardize_column(column_data):
    return (column_data - column_data.mean()) / column_data.std() """

# read the csv file
df_all = pd.read_csv('C:/Users/drewm/Desktop/album_project/output.csv', encoding='utf-8')
df_af_values = pd.read_csv('C:/Users/drewm/Desktop/album_project/output.csv', usecols=[8,9,10,11,12,13,14,15,16], encoding='utf-8')

af_values_array = df_af_values.values

# Initialize a new StandardScaler instance
scaler = StandardScaler()

# Fit the scaler to the data and transform the data
weights = [1, 1, 1, .6, .75, .5, .6, .6, .8]
data_np_scaled = np.round(scaler.fit_transform(af_values_array) * weights, 3)

# if you want to convert the dataframe to a list of lists (where each sub-list is a row)
af_values_all = data_np_scaled.tolist()
all_album_data = df_all.values.tolist()

"""df_af_values = round(((df_af_values - means) / std_devs),3)

all_album_af_values = df_af_values.values.tolist() """

# Standardize all columns
""" def normalize_column(column_data, mean, std_dev):
    return (column_data - mean) / std_dev

# Use the apply method to normalize each column in the DataFrame
for p in range(0,8):
    df_af_values.iloc[p] = normalize_column(df_af_values.iloc[p],means[p],std_devs[p]) """

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

def find_similar_items(sample_stats, all_album_stats, top_n=20):
    data_np = np.array(all_album_stats) # Convert list to numpy array for efficient computation
    item_np = np.array(sample_stats)
    distances = np.sqrt(((data_np - item_np)**2).sum(axis=1)) # Euclidean distance
    closest_indices = distances.argsort()[:top_n] # Get indices of top_n closest items
    #closest_items = [all_album_stats[i] for i in closest_indices]
    #print(max(distances))
    return closest_indices

# Create your views here.
def home_page(request):
    return HttpResponse("Hello, this is my view!")


def print_top_tracks(request):
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                               client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                               scope='user-top-read'))
    #code = 'AQARU7NQuKqlJnB9mm1UHxMMSayerO176rUPqnOHDuOrUVKj39JmPuCthcQYRrv2hGT8OnGf-HPLvx0eZI3HokhOsf0KYWo-rRPi1P4Pmz4i7U4vf9YlBdZh-uwnzadCKTt7hBhuQRjDeL7LFdNKqvMd88bOnBb_ya90_wYMenFiqIwQtQkQxbPzPu87'
    #sp.get_access_token()
    """ access_token = request.session.get('spotify_access_token')
    if access_token:
        # Create a Spotipy object with the access token
        sp = spotipy.Spotify(auth=access_token) """

        # Now you can make Spotify API requests using the sp object

    top_tracks_raw = sp.current_user_top_tracks(limit=20)
    #print(top_tracks_raw)

    all_track_ids = []
    for i in range(0,len(top_tracks_raw['items'])):
        track_id = top_tracks_raw['items'][i]['id']
        all_track_ids.append(track_id)

    query_track_params = {"ids": ",".join(all_track_ids)}
    all_tracks_url = "https://api.spotify.com/v1/audio-features"
    response_track = requests.get(all_tracks_url, headers=headers, params=query_track_params)  
                    
    if response_track.status_code == 200:
        all_tracks_data = response_track.json()
        #print(all_tracks_data)

        af_values = [0,0,0,0,0,0,0,0,0]
        total_tracks = 0
        for n in range(0,len(all_tracks_data['audio_features'])):
            try:
                af_values[0] += all_tracks_data['audio_features'][n]['acousticness']
                af_values[1] += all_tracks_data['audio_features'][n]['danceability']
                af_values[2] += all_tracks_data['audio_features'][n]['energy']
                af_values[3] += all_tracks_data['audio_features'][n]['instrumentalness']
                af_values[4] += all_tracks_data['audio_features'][n]['loudness']
                af_values[5] += all_tracks_data['audio_features'][n]['mode']
                af_values[6] += all_tracks_data['audio_features'][n]['speechiness']
                af_values[7] += all_tracks_data['audio_features'][n]['tempo']
                af_values[8] += all_tracks_data['audio_features'][n]['valence']
                total_tracks += 1
            except:
                total_tracks += 0
        #print(af_values)
        print(total_tracks)
        af_values = [x / total_tracks for x in af_values]

    # Assuming sample_item is your original sample item
    sample_af_values = np.array(af_values).reshape(1, -1)

    # Use the same scaler to transform the sample item
    scaled_af_values = np.round(scaler.transform(sample_af_values),3)
    print(scaled_af_values)
    list_values = scaled_af_values.tolist()

    similar_albums_indices = find_similar_items(list_values, af_values_all)
    #print(similar_albums)
    similar_album_names = []
    for m in range(0,len(similar_albums_indices)):
        album_info = []
        album_name = all_album_data[similar_albums_indices[m]][1]
        album_artist = all_album_data[similar_albums_indices[m]][0]
        album_year = all_album_data[similar_albums_indices[m]][2]
        album_pop = all_album_data[similar_albums_indices[m]][3]
        album_af = data_np_scaled[similar_albums_indices[m]]
        album_info.append(album_name)
        album_info.append(album_artist)
        album_info.append(album_year)
        album_info.append(album_pop)
        album_info.append(album_af)
        similar_album_names.append(album_info)
        
    # Process the data and render the template...
    context = {'similar_albums': similar_album_names, 'top_tracks': scaled_af_values}
    return render(request, 'top_songs.html', context)
    
def callback(request):
    # Get the authorization code from the URL after the user grants access
    code = request.GET.get('code')

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                               client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                               scope='user-top-read'))

    # Fetch the access token using the received authorization code
    sp.auth_manager.get_access_token(code)

    # Redirect the user back to your main page or any other route
    return redirect('home_page')

def all_albums(request):
    sorted_data = sorted(all_album_data, key=lambda x: x['Popularity'], reverse=True)
    return render(request, 'display_album_table.html', {'data': sorted_data})