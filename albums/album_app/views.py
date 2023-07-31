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
from sklearn.cluster import KMeans
from album_app.forms import UserChoiceForm
from django.contrib.auth import logout

client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET

means = []
std_devs = []

""" def standardize_column(column_data):
    return (column_data - column_data.mean()) / column_data.std() """

# read the csv file
df_all = pd.read_csv('C:/Users/drewm/Desktop/album_project/output.csv', encoding='utf-8')
df_af_values = pd.read_csv('C:/Users/drewm/Desktop/album_project/output.csv', usecols=[3,8,9,10,11,12,13,14,15,16], encoding='utf-8')

af_values_array = df_af_values.values

# Initialize a new StandardScaler instance
scaler = StandardScaler()

# Fit the scaler to the data and transform the data
#weights = [1, 1, 1, .6, .75, .5, .6, .6, .8]
data_np_scaled = np.round(scaler.fit_transform(af_values_array), 3)
scaled_data = data_np_scaled.tolist()

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

def weighted_euclidean(a, b, weights):
    q = a - b
    return np.sqrt((weights*q*q).sum())

weights = [.5,1,1,1,1,1,0,0,1,0]



def find_similar_items(sample_stats, all_album_stats, top_n=20):
    data_np = np.array(all_album_stats) # Convert list to numpy array for efficient computation
    item_np = np.array(sample_stats)
    distances = np.array([weighted_euclidean(row, item_np, weights) for row in all_album_stats]) # Euclidean distance
    closest_indices = distances.argsort()[:top_n] # Get indices of top_n closest items
    #closest_items = [all_album_stats[i] for i in closest_indices]
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

    # Now you can make Spotify API requests using the sp object
    top_tracks_raw = sp.current_user_top_tracks(limit=30)

    n_clusters = 20
    kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)

    weights = np.array([.3,2,2,2,2,2,0,1,0,0])

    weighted_data = np.array(scaled_data) * weights
    labels = kmeans.fit_predict(weighted_data)

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
        af_values = [x / total_tracks for x in af_values]

    all_tracks_url = "https://api.spotify.com/v1/tracks"
    response_tracks = requests.get(all_tracks_url, headers=headers, params=query_track_params)  

    if response_tracks.status_code == 200:
        all_tracks_data = response_tracks.json()
        #print(all_tracks_data)

        avg_pop = 0
        total_tracks = 0
        for n in range(0,len(all_tracks_data['tracks'])):
            try:
                avg_pop += all_tracks_data['tracks'][n]['popularity']
                total_tracks += 1
            except:
                total_tracks += 0
        avg_pop /= total_tracks

    # Assuming sample_item is your original sample item
    af_values.insert(0, avg_pop)
    sample_af_values = np.array(af_values).reshape(1, -1)

    # Use the same scaler to transform the sample item
    scaled_af_values = np.round(scaler.transform(sample_af_values),3)
    list_values = scaled_af_values.tolist()

    cluster_label = kmeans.predict(scaled_af_values)
    print(cluster_label)

    same_cluster_indices = [i for i, label in enumerate(labels) if label == cluster_label[0]]

    # Fetch the items from the original list
    same_cluster_items = [all_album_data[i] for i in same_cluster_indices]
    #print(same_cluster_items)

    #print(label)
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
    context = {'similar_albums': same_cluster_items, 'top_tracks': scaled_af_values, 'count': len(all_album_data)}
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
    #sorted_data = sorted(all_album_data, key=lambda x: x['Popularity'], reverse=True)
    return render(request, 'display_album_table.html', {'data': all_album_data})

def user_choice_view(request):
    if request.method == 'POST':
        form = UserChoiceForm(request.POST)
        if form.is_valid():
            form.save()  # Save the user's choice to the database
            return redirect('home_page')  # Redirect to a success page or another URL
    else:
        form = UserChoiceForm()
    return render(request, 'user_choice_form.html', {'form': form})

def logout_view(request):
    # Log the user out using Django's built-in logout function
    #logout(request)
    #code = request.GET.get('code')

    sp = spotipy.oauth2.SpotifyOAuth(client_id=settings.SPOTIFY_CLIENT_ID,
                                               client_secret=settings.SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=settings.SPOTIFY_REDIRECT_URI,
                                               scope='user-top-read')

    # Fetch the access token using the received authorization code
    #sp.auth_manager.get_access_token(code)
    access_token = sp.get_cached_token()['access_token']

    
    if access_token:
        heading = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.post('https://accounts.spotify.com/api/token/revoke',
                                 data={'token': access_token},
                                 headers=heading)

        if response.status_code == 200:
            # Access token successfully revoked
            print("Access token revoked.")
        else:
            # Failed to revoke access token
            print(response.status_code)
            print("Failed to revoke access token.")

    # Redirect the user to a page after logging out (replace 'home' with the desired URL)
    return redirect('home_page')