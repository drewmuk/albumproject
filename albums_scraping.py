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

def get_albums_data(artist_ids, other_album_ids, spanish_artists, omit_ids, test):
    access_token = get_access_token(client_id, client_secret)
    last_access_time = time.time()
    # Headers for the eventual table
    all_albums = [['Artist','Album','Year','Popularity','Length (Min)', 'Album Cover',
                   'ID', 'Language',
                   'acousticness','danceability','energy','instrumentalness',
                   'loudness','mode','speechiness','tempo','valence', 'liveness']]
    
    highest_ac = []; lowest_ac = []
    highest_da = []; lowest_da = []
    highest_en = []; lowest_en = []
    highest_in = []; lowest_in = []
    highest_lo = []; lowest_lo = []
    highest_mo = []; lowest_mo = []
    highest_sp = []; lowest_sp = []
    highest_te = []; lowest_te = []
    highest_va = []; lowest_va = []

    cutoff = 30

    # Start by iterating over all the artists I want to include
    for i in range(0,len(artist_ids)):
        if time.time() - last_access_time > 3200:
            access_token = get_access_token(client_id, client_secret)
            last_access_time = time.time()

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        if not test:
            time.sleep(1.5)

        language = "English"

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
                if album_id not in omit_ids:
                    all_album_ids.append(album_id)

            query_album_params = {"ids": ",".join(all_album_ids)}
            all_albums_url = "https://api.spotify.com/v1/albums"
            response_album = requests.get(all_albums_url, headers=headers, params=query_album_params)

            if response_album.status_code == 200:
                all_albums_data = response_album.json()
                print(all_albums_data['albums'][0]['artists'][0]['name'])
                for k in range(0, len(all_albums_data['albums'])):
                    if not test:
                        time.sleep(1)
                    all_track_ids = []

                    total_duration_ms = 0
                    for m in range(0,len(all_albums_data['albums'][k]['tracks']['items'])):
                        total_duration_ms += all_albums_data['albums'][k]['tracks']['items'][m]['duration_ms']
                        track_id = all_albums_data['albums'][k]['tracks']['items'][m]['id']
                        all_track_ids.append(track_id)
                    
                    duration_min = round((total_duration_ms/1000/60),1)
                    popularity = all_albums_data['albums'][k]['popularity']

                    if duration_min < 24 or popularity < 30:
                        continue
                    
                    print(all_albums_data['albums'][k]['name'])
                    album_cover_url = all_albums_data['albums'][k]["images"][0]["url"]
                    
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

                                if len(highest_ac) < cutoff:
                                    # If the list of highest tracks is not yet filled with X tracks, add the current track to the list
                                    highest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                else:
                                    # If the list is full, find the lowest track in the list of highest tracks and replace it with the current track if the current track is higher
                                    min_ac = min(highest_ac, key=lambda x: x[1])
                                    if ac > min_ac[1]:
                                        highest_ac.remove(min_ac)
                                        highest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                if len(lowest_ac) < cutoff:
                                    lowest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                else:
                                    max_ac = max(lowest_ac, key=lambda x: x[1])
                                    if ac < max_ac[1]:
                                        lowest_ac.remove(max_ac)
                                        lowest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))

                                # danceability
                                if len(highest_da) < cutoff:
                                    highest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                else:
                                    min_da = min(highest_da, key=lambda x: x[1])
                                    if da > min_da[1]:
                                        highest_da.remove(min_da)
                                        highest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                if len(lowest_da) < cutoff:
                                    lowest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                else:
                                    max_da = max(lowest_da, key=lambda x: x[1])
                                    if da < max_da[1]:
                                        lowest_da.remove(max_da)
                                        lowest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))

                                # energy
                                if len(highest_en) < cutoff:
                                    highest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                else:
                                    min_en = min(highest_en, key=lambda x: x[1])
                                    if en > min_en[1]:
                                        highest_en.remove(min_en)
                                        highest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                if len(lowest_en) < cutoff:
                                    lowest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                else:
                                    max_en = max(lowest_en, key=lambda x: x[1])
                                    if en < max_en[1]:
                                        lowest_en.remove(max_en)
                                        lowest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))

                                # instrumentalness
                                if len(highest_in) < cutoff:
                                    highest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                else:
                                    min_in = min(highest_in, key=lambda x: x[1])
                                    if ins > min_in[1]:
                                        highest_in.remove(min_in)
                                        highest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                if len(lowest_in) < cutoff:
                                    lowest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                else:
                                    max_in = max(lowest_in, key=lambda x: x[1])
                                    if ins < max_in[1]:
                                        lowest_in.remove(max_in)
                                        lowest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                
                                # loudness
                                if len(highest_lo) < cutoff:
                                    highest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                else:
                                    min_lo = min(highest_lo, key=lambda x: x[1])
                                    if lo > min_lo[1]:
                                        highest_lo.remove(min_lo)
                                        highest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                if len(lowest_lo) < cutoff:
                                    lowest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                else:
                                    max_lo = max(lowest_lo, key=lambda x: x[1])
                                    if lo < max_lo[1]:
                                        lowest_lo.remove(max_lo)
                                        lowest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))

                                # mode
                                if len(highest_mo) < cutoff:
                                    highest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                else:
                                    min_mo = min(highest_mo, key=lambda x: x[1])
                                    if mo > min_mo[1]:
                                        highest_mo.remove(min_mo)
                                        highest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                if len(lowest_mo) < cutoff:
                                    lowest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                else:
                                    max_mo = max(lowest_mo, key=lambda x: x[1])
                                    if mo < max_mo[1]:
                                        lowest_mo.remove(max_mo)
                                        lowest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))

                                # speechiness
                                if len(highest_sp) < cutoff:
                                    highest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                else:
                                    min_sp = min(highest_sp, key=lambda x: x[1])
                                    if sp > min_sp[1]:
                                        highest_sp.remove(min_sp)
                                        highest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                if len(lowest_sp) < cutoff:
                                    lowest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                else:
                                    max_sp = max(lowest_sp, key=lambda x: x[1])
                                    if sp < max_sp[1]:
                                        lowest_sp.remove(max_sp)
                                        lowest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))

                                # tempo
                                if len(highest_te) < cutoff:
                                    highest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                else:
                                    min_te = min(highest_te, key=lambda x: x[1])
                                    if te > min_te[1]:
                                        highest_te.remove(min_te)
                                        highest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                if len(lowest_te) < cutoff:
                                    lowest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                else:
                                    max_te = max(lowest_te, key=lambda x: x[1])
                                    if te < max_te[1]:
                                        lowest_te.remove(max_te)
                                        lowest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))

                                # valence
                                if len(highest_va) < cutoff:
                                    highest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                else:
                                    min_va = min(highest_va, key=lambda x: x[1])
                                    if va > min_va[1]:
                                        highest_va.remove(min_va)
                                        highest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                if len(lowest_va) < cutoff:
                                    lowest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                else:
                                    max_va = max(lowest_va, key=lambda x: x[1])
                                    if va < max_va[1]:
                                        lowest_va.remove(max_va)
                                        lowest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
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

        language = "English"

        other_album_id = other_album_ids[s]
        other_album_url = f"https://api.spotify.com/v1/albums/{other_album_id}"
        response_other_album = requests.get(other_album_url, headers=headers)

        if response_other_album.status_code == 200:
            other_album_data = response_other_album.json()
            all_track_ids = []

            total_duration_ms = 0
            for m in range(0,len(other_album_data['tracks']['items'])):
                total_duration_ms += other_album_data['tracks']['items'][m]['duration_ms']
                track_id = other_album_data['tracks']['items'][m]['id']
                all_track_ids.append(track_id)
                    
            duration_min = round((total_duration_ms/1000/60),1)
            popularity = other_album_data['popularity']

            if duration_min < 24 or popularity < 25:
                continue
                    
            other_album_cover_url = other_album_data["images"][0]["url"]
                    
            query_track_params = {"ids": ",".join(all_track_ids)}
            all_tracks_url = "https://api.spotify.com/v1/audio-features"
            response_track = requests.get(all_tracks_url, headers=headers, params=query_track_params)  
                     
            if response_track.status_code == 200:
                all_tracks_data = response_track.json()
                af_values = [0,0,0,0,0,0,0,0,0,0]
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

                                if len(highest_ac) < cutoff:
                                    # If the list of highest tracks is not yet filled with X tracks, add the current track to the list
                                    highest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                else:
                                    # If the list is full, find the lowest track in the list of highest tracks and replace it with the current track if the current track is higher
                                    min_ac = min(highest_ac, key=lambda x: x[1])
                                    if ac > min_ac[1]:
                                        highest_ac.remove(min_ac)
                                        highest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                if len(lowest_ac) < cutoff:
                                    lowest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))
                                else:
                                    max_ac = max(lowest_ac, key=lambda x: x[1])
                                    if ac < max_ac[1]:
                                        lowest_ac.remove(max_ac)
                                        lowest_ac.append((all_tracks_data['audio_features'][n]['id'], ac, "ac"))

                                # danceability
                                if len(highest_da) < cutoff:
                                    highest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                else:
                                    min_da = min(highest_da, key=lambda x: x[1])
                                    if da > min_da[1]:
                                        highest_da.remove(min_da)
                                        highest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                if len(lowest_da) < cutoff:
                                    lowest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))
                                else:
                                    max_da = max(lowest_da, key=lambda x: x[1])
                                    if da < max_da[1]:
                                        lowest_da.remove(max_da)
                                        lowest_da.append((all_tracks_data['audio_features'][n]['id'], da, "da"))

                                # energy
                                if len(highest_en) < cutoff:
                                    highest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                else:
                                    min_en = min(highest_en, key=lambda x: x[1])
                                    if en > min_en[1]:
                                        highest_en.remove(min_en)
                                        highest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                if len(lowest_en) < cutoff:
                                    lowest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))
                                else:
                                    max_en = max(lowest_en, key=lambda x: x[1])
                                    if en < max_en[1]:
                                        lowest_en.remove(max_en)
                                        lowest_en.append((all_tracks_data['audio_features'][n]['id'], en, "en"))

                                # instrumentalness
                                if len(highest_in) < cutoff:
                                    highest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                else:
                                    min_in = min(highest_in, key=lambda x: x[1])
                                    if ins > min_in[1]:
                                        highest_in.remove(min_in)
                                        highest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                if len(lowest_in) < cutoff:
                                    lowest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                else:
                                    max_in = max(lowest_in, key=lambda x: x[1])
                                    if ins < max_in[1]:
                                        lowest_in.remove(max_in)
                                        lowest_in.append((all_tracks_data['audio_features'][n]['id'], ins, "ins"))
                                
                                # loudness
                                if len(highest_lo) < cutoff:
                                    highest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                else:
                                    min_lo = min(highest_lo, key=lambda x: x[1])
                                    if lo > min_lo[1]:
                                        highest_lo.remove(min_lo)
                                        highest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                if len(lowest_lo) < cutoff:
                                    lowest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))
                                else:
                                    max_lo = max(lowest_lo, key=lambda x: x[1])
                                    if lo < max_lo[1]:
                                        lowest_lo.remove(max_lo)
                                        lowest_lo.append((all_tracks_data['audio_features'][n]['id'], lo, "lo"))

                                # mode
                                if len(highest_mo) < cutoff:
                                    highest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                else:
                                    min_mo = min(highest_mo, key=lambda x: x[1])
                                    if mo > min_mo[1]:
                                        highest_mo.remove(min_mo)
                                        highest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                if len(lowest_mo) < cutoff:
                                    lowest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))
                                else:
                                    max_mo = max(lowest_mo, key=lambda x: x[1])
                                    if mo < max_mo[1]:
                                        lowest_mo.remove(max_mo)
                                        lowest_mo.append((all_tracks_data['audio_features'][n]['id'], mo, "mo"))

                                # speechiness
                                if len(highest_sp) < cutoff:
                                    highest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                else:
                                    min_sp = min(highest_sp, key=lambda x: x[1])
                                    if sp > min_sp[1]:
                                        highest_sp.remove(min_sp)
                                        highest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                if len(lowest_sp) < cutoff:
                                    lowest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))
                                else:
                                    max_sp = max(lowest_sp, key=lambda x: x[1])
                                    if sp < max_sp[1]:
                                        lowest_sp.remove(max_sp)
                                        lowest_sp.append((all_tracks_data['audio_features'][n]['id'], sp, "sp"))

                                # tempo
                                if len(highest_te) < cutoff:
                                    highest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                else:
                                    min_te = min(highest_te, key=lambda x: x[1])
                                    if te > min_te[1]:
                                        highest_te.remove(min_te)
                                        highest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                if len(lowest_te) < cutoff:
                                    lowest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))
                                else:
                                    max_te = max(lowest_te, key=lambda x: x[1])
                                    if te < max_te[1]:
                                        lowest_te.remove(max_te)
                                        lowest_te.append((all_tracks_data['audio_features'][n]['id'], te, "te"))

                                # valence
                                if len(highest_va) < cutoff:
                                    highest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                else:
                                    min_va = min(highest_va, key=lambda x: x[1])
                                    if va > min_va[1]:
                                        highest_va.remove(min_va)
                                        highest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                if len(lowest_va) < cutoff:
                                    lowest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                else:
                                    max_va = max(lowest_va, key=lambda x: x[1])
                                    if va < max_va[1]:
                                        lowest_va.remove(max_va)
                                        lowest_va.append((all_tracks_data['audio_features'][n]['id'], va, "va"))
                                total_tracks += 1
                    except:
                        total_tracks += 0
                            
                af_values = [round(x / total_tracks,3) for x in af_values]

            
                temp = [other_album_data['artists'][0]['name'],
                        other_album_data['name'],
                        other_album_data['release_date'][:4], 
                        popularity, duration_min, other_album_cover_url, 
                        other_album_id, language]
                for p in range(0,len(af_values)):
                    temp.append(af_values[p])
                print(other_album_data['name'])
                all_albums.append(temp)

        else:
            print(response_other_album.status_code)

    lists_names = ['high acousticness','high danceability','high energy','high instrumentalness',
                   'high loudness','high mode','high speechiness','high tempo','high valence',
                   'low acousticness','low danceability','low energy','low instrumentalness',
                   'low loudness','low mode','low speechiness','low tempo','low valence']
    lists_data = [highest_ac, highest_da, highest_en, highest_in, highest_lo, highest_mo,
                  highest_sp, highest_te, highest_va, lowest_ac, lowest_da, lowest_en,
                  lowest_in, lowest_lo, lowest_mo, lowest_sp, lowest_va]
    
    all_track_info = []
    track_ids = [item[0] for lst in lists_data for item in lst]
    for i in range(0, len(track_ids)):
        track_info = find_track_info(track_ids[i])
        all_track_info.append(track_info)

    placeholder_dict = {}
    track_id_to_feature = {}

    key_placeholder = 0
    for sublist in lists_data:
        for track_id, feature_value, type in sublist:
            placeholder_dict[key_placeholder] = (track_id, feature_value, type)
            key_placeholder += 1

    for key, value in placeholder_dict.items():
        track_id = value[0]
        data = (value[1], value[2])
        track_id_to_feature[track_id] = data


    combined_list = [[artist_name, track_name, track_id, track_id_to_feature[track_id][0], 
                      track_id_to_feature[track_id][1]] for artist_name, track_name, track_id in all_track_info]
    
    with open("C:/Users/drewm/Desktop/album_project/extreme_vals.csv", mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Artist Name', 'Track Name', 'Track ID', 'Value', 'Type'])  # Write the header row

        for data in combined_list:
            writer.writerow(data)

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
            print(response_search.status_code)
            print("Search failed")

    return artist_ids

def find_track_info(track_id):
    search_url = f"https://api.spotify.com/v1/tracks/{track_id}"

    access_token = get_access_token(client_id, client_secret)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    track_info = []

    response_search = requests.get(search_url, headers=headers)
    if response_search.status_code == 200:
        all_track_info = response_search.json()

        track_info.append(all_track_info["artists"][0]['name'])
        track_info.append(all_track_info["name"])
        track_info.append(all_track_info["id"])
    elif response_search.status_code == 401:
        print("Authorization code expired")
    else:
        print("Search failed")

    return track_info

def find_album_ids(album_names, by_names):
    album_ids = []
    search_url = "https://api.spotify.com/v1/search"

    access_token = get_access_token(client_id, client_secret)

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    for q in range(0,len(album_names)):
        album_name = album_names[q]
        by_name = by_names[q]
        query_album_params = {
            'q': f'artist:{by_name} album:{album_name}',
            "type": "album"
        }

        response_search = requests.get(search_url, headers=headers, params=query_album_params)
        if response_search.status_code == 200:
            search_results = response_search.json()

            # Extract artist details from the search results
            albums = search_results["albums"]["items"]
            if len(albums) > 0:
                album = albums[0]  # Get the first matching album
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

omit_ids = []

test = 1

# File path of the CSV file
if test:
    artist_file_path = "C:/Users/drewm/Desktop/album_project/input_artists_test.csv"
    output_file_path = 'C:/Users/drewm/Desktop/album_project/test_output.csv'
else:
    artist_file_path = "C:/Users/drewm/Desktop/album_project/input_artists.csv"
    output_file_path = 'C:/Users/drewm/Desktop/album_project/output.csv'

album_file_path = "C:/Users/drewm/Desktop/album_project/input_albums.csv"
language_file_path = "C:/Users/drewm/Desktop/album_project/languages.csv"
omit_file_path = "C:/Users/drewm/Desktop/album_project/omit_albums.csv"

# Read the Input Artists CSV
with open(artist_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        artist_name = row["Artist Name"]
        artist_names.append(artist_name)

# Read the Input Albums CSV
with open(album_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        album_name = row["Album Name"]
        by_name = row["By"]
        album_names.append(album_name)
        by_names.append(by_name)

# Read the Spanish Artists CSV
with open(language_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        spanish_artist = row["Artist Name"]
        spanish_names.append(spanish_artist)

# Read the Omit Albums CSV
with open(omit_file_path, "r", newline="") as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        album_id = row["ID"]
        omit_ids.append(album_id)

start_time = time.time()

artist_ids = find_artist_ids(artist_names, test)
album_ids = find_album_ids(album_names, by_names)
#spanish_artists = find_artist_ids(spanish_names, test)
spanish_artists = ['2R21vXR83lH98kGeO99Y66', '4SsVbpTthjScTS7U2hmr1X', '1qto4hHid1P71emI6Fd8xi', '1mux8L6xg2Cmrc7k0wQczl', 
                   '4q3ewBCX7sLwd24euuV69X', '4obzFoKoKRHIphyHzJ35G3', '09xj0S68Y1OU1vHMCZAIvz', '28gNT5KBp7IjEOQoevXf9N', 
                   '0eecdvMrqBftK0M1VKhaF4', '4VMYDCV2IEDYJArk749S6m', '0KPX4Ucy9dk82uj4GpKesn', '2oQX8QiMXOyuqbcZEFsZfm', 
                   '329e4yvIujISKGKz1BZZbO', '2LRoIwlKmHjgvigdNGBHNo', '1QOmebWGB6FdFtW7Bo3F0W', '1vyhD5VmyZ7KMfW5gqLgo5', 
                   '6nVcHLIgY5pE2YCl8ubca1', '2QWIScpFDNxmS6ZEMIUvgm', '1U1el3k54VvEUzo3ybLPlM', '790FomKkXshlbRYZFtlgla', 
                   '4TK1gDgb7QKoPFlzRrBRgR', '2mSHY8JOR0nRi3mtHqVa04', '47MpMsUfWtgyIIBEFOr4FE', '1r4hJ1h58CWwUQe3MxPuau', 
                   '7okwEbXzyT2VffBmyQBWLz', '0tmwSHipWxN12fsoLcFU3B', '1DxLCyH42yaHKGK3cl5bvG', '4boI7bJtmB1L3b1cuL75Zr', 
                   '0Q8NcsJwoCbZOHHW63su5S', '5C4PDR4LnhZTbVnKWXuDKD', '1hcdI2N1023RvSwLzTtdsp', '1SupJlEpv7RS2tPNRaHViT', 
                   '5hdhHgpxyniooUiQVaPxQ0', '1i8SpTcr7yvPOmcqrbnVXY', '3vQ0GE3mI0dAaxIMYe5g7z', '4QVBYiagIaa6ZGSPMbybpy', 
                   '12GqGscKJx3aE4t07u7eVZ', '4bw2Am3p9ji3mYsXNXtQcd', '3MHaV05u0io8fQbZ2XPtlC', '52iwsT98xCoGgiGntTiR7K', 
                   '1mcTU81TzQhprhouKaTkpq', '0vR2qb8m9WHeZ5ByCbimq2', '2IMZYfNi21MGqxopj9fWx8', '5lwmRuXgjX8xIwlnauTZIP', 
                   '7ltDVBr6mKbRvohxheJ9h1', '07YUOmWljBTXwIseAUd9TW', '77ziqFxp5gaInVrF2lj4ht', '0EmeFodog0BfCgMzAIvKQp', 
                   '7An4yvF7hDYDolN4m5zKBp', '0GM7qgcRCORpGnfcN2tCiB', '5Y3MV9DZ0d87NnVm56qSY1', '1wZtkThiXbVNtj6hee6dz9', 
                   '21451j1KhjAiaYKflxBjr1', '6IdtcAwaNVAggwd6sCKgTI']

all_albums = get_albums_data(artist_ids, album_ids, spanish_artists, omit_ids, test)

with open(output_file_path, "w", newline="", encoding="utf-8") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerows(all_albums)

print("CSV file has been created successfully.")

end_time = time.time()
elapsed_time = end_time - start_time
elapsed_min = round((elapsed_time / 60),1)
print(f"Script execution time: {elapsed_min:.2f} minutes")
