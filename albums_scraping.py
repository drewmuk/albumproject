import requests
from PIL import Image
from io import BytesIO

# Get the API access token (updates every hour)

""" def get_access_token(client_id, client_secret):
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

client_id = "7ac4e70ee1f04c3aae177b5e0e1f060a"
client_secret = ""

access_token = get_access_token(client_id, client_secret)
if access_token:
    print("Access Token:", access_token) """

# current access token so I don't have to keep running the above code every time
access_token = 'BQBTu69_DY4bYS8lWYvwue9JV0WlaJIydnCzIo3zxkv414vja-8ROLtm9qUeF2Qq_4xwIPiK0tSAwhDcqvHbGh3bMq3Eq_qiwaeHmeqswVjzAEn80MI'
def get_albums_data(artist_ids, access_token):

    # Set the "Authorization" header with the access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Headers for the eventual table
    all_albums = [['Artist','Album','Popularity','Length (Min)',
                   'acousticness','danceability','energy','instrumentalness',
                   'loudness','mode','speechiness','tempo','valence']]

    # Start by iterating over all the artists I want to include
    for i in range(0,len(artist_ids)):
        indiv_id = artist_ids[i]
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
                for k in range(0, len(all_albums_data['albums'])):
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
                    
                    popularity = all_albums_data['albums'][k]['popularity']
                    total_duration_ms = 0

                    all_track_ids = []
                    for m in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
                        total_duration_ms += all_albums_data['albums'][k]['tracks']['items'][m]['duration_ms']
                        track_id = all_albums_data['albums'][k]['tracks']['items'][m]['id']
                        all_track_ids.append(track_id)

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
                        af_values = [0,0,0,0,0,0,0,0,0]
                        
                        for n in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
                        
                            af_values[0] += all_tracks_data['audio_features'][n]['acousticness']
                            af_values[1] += all_tracks_data['audio_features'][n]['danceability']
                            af_values[2] += all_tracks_data['audio_features'][n]['energy']
                            af_values[3] += all_tracks_data['audio_features'][n]['instrumentalness']
                            af_values[4] += all_tracks_data['audio_features'][n]['loudness']
                            af_values[5] += all_tracks_data['audio_features'][n]['mode']
                            af_values[6] += all_tracks_data['audio_features'][n]['speechiness']
                            af_values[7] += all_tracks_data['audio_features'][n]['tempo']
                            af_values[8] += all_tracks_data['audio_features'][n]['valence']
                            
                        af_values = [round(x / len(all_albums_data['albums'][k]['tracks']['items']),3) for x in af_values]
                        #average_audio_features = dict(zip(af_keys,af_values))


                    duration_min = round((total_duration_ms/1000/60),1)
                    if all_albums_data['albums'][k]['artists'][0]['id'] == indiv_id:
                        temp = [all_albums_data['albums'][k]['artists'][0]['name'],
                                all_albums_data['albums'][k]['name'], popularity, duration_min, album_cover_url]
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

    return all_albums
    
# List of all the artist IDs I want to include, right now I'm just testing with Bad Bunny and Tyler
artist_ids = ['4q3ewBCX7sLwd24euuV69X','4V8LLVI7PbaPR0K2TGSxFF']

all_albums = get_albums_data(artist_ids, access_token)
if all_albums:
    print("Albums Data:")
    print(all_albums)
