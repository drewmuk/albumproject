import requests
from PIL import Image
from io import BytesIO
import csv
import time
from albums.albums import settings

# Get the API access token (updates every hour)

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

client_id = settings.SPOTIFY_CLIENT_ID
client_secret = settings.SPOTIFY_CLIENT_SECRET

""" access_token = get_access_token(client_id, client_secret)
if access_token:
    print("Access Token:", access_token)

# current access token so I don't have to keep running the above code every time
access_token = 'BQAwEVwV1Sxb5I2xuwRu38FgdizY2yqtx_asybL-xoF9MUlEeBTamhNXW72KZCevzRkY2JxF-iQgsgItM1TM9XlsTE4zmbaREjX2yC7aLHmHjbBXUIU' """

def get_albums_data(artist_ids, other_album_ids, spanish_artists, test):
    access_token = get_access_token(client_id, client_secret)
    last_access_time = time.time()
    # Headers for the eventual table
    all_albums = [['Artist','Album','Year','Popularity','Length (Min)', 'Album Cover',
                   'ID', 'Language',
                   'acousticness','danceability','energy','instrumentalness',
                   'loudness','mode','speechiness','tempo','valence', 'liveness']]
    
    language = "English"

    # Start by iterating over all the artists I want to include
    for i in range(0,len(artist_ids)):
        if time.time() - last_access_time > 3200:
            access_token = get_access_token(client_id, client_secret)
            last_access_time = time.time()

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        if not test:
            time.sleep(2)
        indiv_id = artist_ids[i]
        if indiv_id in spanish_artists:
            language = "Spanish"

        artist_url = f"https://api.spotify.com/v1/artists/{artist_ids[i]}/albums?include_groups=album" # filter out singles, comps, etc.

        # Make a GET request to get the album data
        response_artist = requests.get(artist_url, headers=headers)

        # Check if the request was successful
        if response_artist.status_code == 200:
            # Parse the response JSON to access the album data
            artist_data = response_artist.json()
            all_album_ids = []
            for j in range(0,len(artist_data['items'])):
                album_id = artist_data['items'][j]['id']
                all_album_ids.append(album_id)

            query_album_params = {"ids": ",".join(all_album_ids)}
            all_albums_url = "https://api.spotify.com/v1/albums"
            response_album = requests.get(all_albums_url, headers=headers, params=query_album_params)

            if response_album.status_code == 200:
                all_albums_data = response_album.json()
                #print(all_albums_data['albums'][0]['artists'][0]['name'])
                for k in range(0, len(all_albums_data['albums'])):
                    if not test:
                        time.sleep(2)
                    all_track_ids = []

                    total_duration_ms = 0
                    for m in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
                        total_duration_ms += all_albums_data['albums'][k]['tracks']['items'][m]['duration_ms']
                        track_id = all_albums_data['albums'][k]['tracks']['items'][m]['id']
                        all_track_ids.append(track_id)
                    
                    duration_min = round((total_duration_ms/1000/60),1)
                    popularity = all_albums_data['albums'][k]['popularity']

                    if duration_min < 25 or popularity < 25:
                        continue
                    
                    print(all_albums_data['albums'][k]['name'])
                    album_cover_url = all_albums_data['albums'][k]["images"][0]["url"]

                    # Download the image using requests
                    """ image_response = requests.get(album_cover_url)
                    if image_response.status_code == 200:
                        # Convert the image content to a PIL image
                        image = Image.open(BytesIO(image_response.content))

                        # Display the image (you can also save it to a file)
                        image.show()

                    else:
                        print("Failed to download the album art.") """
                    
                    query_track_params = {"ids": ",".join(all_track_ids)}
                    all_tracks_url = "https://api.spotify.com/v1/audio-features"
                    response_track = requests.get(all_tracks_url, headers=headers, params=query_track_params)  
                    
                    if response_track.status_code == 200:
                        all_tracks_data = response_track.json()

                        # omitting liveness for the moment (prbability that track was performed live)
                        # also omitting duration, key, and time_signature
                        # acousticness = 0; danceability = 0; energy = 0; instrumentalness = 0; loudness = 0
                        # mode = 0; speechiness = 0; tempo = 0; valence = 0
                        #af_keys = ['acousticness','danceability','energy','instrumentalness','loudness','mode','speechiness','tempo','valence']
                        af_values = [0,0,0,0,0,0,0,0,0,0]
                        total_tracks = 0
                        for n in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
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
                                af_values[9] += all_tracks_data['audio_features'][n]['liveness']
                                total_tracks += 1
                            except:
                                total_tracks += 0

                        af_values = [round(x / total_tracks,3) for x in af_values]
                        if af_values[9] > .5:
                            continue
                        #average_audio_features = dict(zip(af_keys,af_values))
                    elif response_track.status_code == 429:
                        print("Too many requests", response_track.headers.get('Retry-After'))
                    else:
                        print("Error:",response_track.status_code)
                        
                    if all_albums_data['albums'][k]['artists'][0]['id'] == indiv_id:
                        temp = [all_albums_data['albums'][k]['artists'][0]['name'],
                                all_albums_data['albums'][k]['name'],
                                all_albums_data['albums'][k]['release_date'][:4], 
                                popularity, duration_min, album_cover_url,
                                all_albums_data['albums'][k]['id'], language]
                        for p in range(0,len(af_values)):
                            temp.append(af_values[p])
                        all_albums.append(temp)
                    
            else:
                print("Failed on individual album level")
                return None

        elif response_artist.status_code == 401:
            print("Authorization code expired")
            return None
        else:
            # Handle the error if the request was unsuccessful
            print("Error code:", response_artist.status_code)
            print("Failed on artist level")
            return None
        
    
    for s in range(0, len(other_album_ids)):
        if time.time() - last_access_time > 3200:
            access_token = get_access_token(client_id, client_secret)
            last_access_time = time.time()

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        other_album_id = other_album_ids[s]
        other_album_url = "https://api.spotify.com/v1/albums/f{other_album_id}"
        response_other_album = requests.get(other_album_url, headers=headers)

        if response_other_album.status_code == 200:
            other_album_data = response_other_album.json()
            #print(all_albums_data['albums'][0]['artists'][0]['name'])
            all_track_ids = []

            total_duration_ms = 0
            for m in range(0,len(other_album_data['tracks']['items'])):
                total_duration_ms += other_album_data['tracks']['items'][m]['duration_ms']
                track_id = other_album_data['tracks']['items'][m]['id']
                all_track_ids.append(track_id)
                    
            duration_min = round((total_duration_ms/1000/60),1)
            popularity = other_album_data['popularity']

            if duration_min < 25 or popularity < 25:
                continue
                    
            #print(other_album_data['name'])
            other_album_cover_url = other_album_data["images"][0]["url"]

            # Download the image using requests
            """ image_response = requests.get(album_cover_url)
            if image_response.status_code == 200:
                # Convert the image content to a PIL image
                image = Image.open(BytesIO(image_response.content))

                # Display the image (you can also save it to a file)
                image.show()

            else:
                print("Failed to download the album art.") """
                    
            query_track_params = {"ids": ",".join(all_track_ids)}
            all_tracks_url = "https://api.spotify.com/v1/audio-features"
            response_track = requests.get(all_tracks_url, headers=headers, params=query_track_params)  
                     
            if response_track.status_code == 200:
                all_tracks_data = response_track.json()
                        #print(all_tracks_data)

                    # omitting liveness for the moment (prbability that track was performed live)
                    # also omitting duration, key, and time_signature
                    # acousticness = 0; danceability = 0; energy = 0; instrumentalness = 0; loudness = 0
                    # mode = 0; speechiness = 0; tempo = 0; valence = 0
                        #af_keys = ['acousticness','danceability','energy','instrumentalness','loudness','mode','speechiness','tempo','valence']
                af_values = [0,0,0,0,0,0,0,0,0,0]
                total_tracks = 0
                for n in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
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
                        af_values[9] += all_tracks_data['audio_features'][n]['liveness']
                        total_tracks += 1
                    except:
                        total_tracks += 0
                            
                af_values = [round(x / total_tracks,3) for x in af_values]
                if af_values[9] > .5:
                    continue
                #average_audio_features = dict(zip(af_keys,af_values))

            
                temp = [other_album_data['artists'][0]['name'],
                        other_album_data['name'],
                        other_album_data['release_date'], 
                        popularity, duration_min, other_album_cover_url, language]
                for p in range(0,len(af_values)):
                    temp.append(af_values[p])
                all_albums.append(temp)

    return all_albums

def find_artist_ids(artist_names, test):
    search_url = "https://api.spotify.com/v1/search"
    artist_ids = []

    access_token = get_access_token(client_id, client_secret)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    for q in range(0,len(artist_names)):
        query_artist_params = {
            "q": artist_names[q],
            "type": "artist"
        }

        response_search = requests.get(search_url, headers=headers, params=query_artist_params)
        if response_search.status_code == 200:
            search_results = response_search.json()

            # Extract artist details from the search results
            artists = search_results["artists"]["items"]
            if len(artists) > 0:
                artist = artists[0]  # Get the first matching artist
                artist_id = artist["id"]
                artist_ids.append(artist_id)
            else:
                print("Artist not found.")
        elif response_search.status_code == 401:
            print("Authorization code expired")
        else:
            print("Search failed")

    return artist_ids

def find_album_ids(album_names, by_names):
    album_ids = []
    search_url = "https://api.spotify.com/v1/search"

    access_token = get_access_token(client_id, client_secret)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    for q in range(0,len(album_names)):
        query_album_params = {
            "q": album_names[q],
            #"artist": by_names[q],
            "type": "album"
        }

        response_search = requests.get(search_url, headers=headers, params=query_album_params)
        if response_search.status_code == 200:
            search_results = response_search.json()

            # Extract artist details from the search results
            albums = search_results["albums"]["items"]
            if len(albums) > 0:
                album = albums[0]  # Get the first matching artist
                album_id = album["id"]
                album_ids.append(album_id)
            else:
                print("Album not found.")
        elif response_search.status_code == 401:
            print("Authorization code expired")
        else:
            print(response_search.status_code)
            print("Search failed")

    return album_ids

# List of all the artist IDs I want to include
artist_names = []

album_names = []
by_names = []

spanish_names = []

test = 0

# File path of the CSV file
if test:
    artist_file_path = "C:/Users/drewm/Desktop/album_project/input_artists_test.csv"
    output_file_path = 'C:/Users/drewm/Desktop/album_project/test_output.csv'
else:
    artist_file_path = "C:/Users/drewm/Desktop/album_project/input_artists.csv"
    output_file_path = 'C:/Users/drewm/Desktop/album_project/output.csv'

album_file_path = "C:/Users/drewm/Desktop/album_project/input_albums.csv"
language_file_path = "C:/Users/drewm/Desktop/album_project/languages.csv"

# Read the CSV file and extract the IDs
with open(artist_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        artist_name = row["Artist Name"]
        artist_names.append(artist_name)

with open(album_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        album_name = row["Album Name"]
        by_name = row["By"]
        album_names.append(album_name)
        by_names.append(by_name)

with open(language_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        spanish_artist = row["Artist Name"]
        spanish_names.append(spanish_artist)

artist_ids = find_artist_ids(artist_names, test)
album_ids = find_album_ids(album_names, by_names)
spanish_artists = find_artist_ids(spanish_names, test)

start_time = time.time()
all_albums = get_albums_data(artist_ids, album_ids, spanish_artists, test)
""" if all_albums:
    print("Albums Data:")
    print(all_albums) """

with open(output_file_path, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(all_albums)

print("CSV file has been created successfully.")

end_time = time.time()
elapsed_time = end_time - start_time
elapsed_min = round((elapsed_time / 60),1)
print(f"Script execution time: {elapsed_min:.2f} minutes")
