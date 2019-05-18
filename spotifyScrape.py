import pandas as pd
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Scrape & organize artist's songs

# client_id = authentication
# client_secret = authentication
# artist_name = artist to search (ex: Kanye West)
# additional_artists = additional artists to include in returned search (ex: 'KIDS SEE GHOSTS')
# min_album_songs = minimum number of songs to include in each returned album
# min_seconds = minimum number of seconds in song
def spotifyScrape(client_id, client_secret, artist_name, additional_artists=[], min_album_songs=5, min_seconds=90, verbose=1):
    
    # User authentication
    scc = SpotifyClientCredentials(client_id=client_id, 
                               client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=scc)
    
    
    ########### Artist & album IDs ###########
    
    # Collect artist ID
    id_search_results = sp.search(artist_name, limit=50)
    try:
        artist_id = [i['artists'][0]['id'] for i in id_search_results['tracks']['items'] if i['artists'][0]['name']==artist_name][0]
    except:
        potential_artists = sorted(set([item['artists'][0]['name'] for item in id_search_results['tracks']['items']]))
        if potential_artists != []:
            return(f"No results found for {artist_name}. Did you mean: {', '.join(potential_artists)}?")
        else:
            return(f"No results found for {artist_name}.")
    
    # Collect album IDs
    album_search_results = sp.artist_albums(artist_id=artist_id, limit=50)
    chosen_albums = {}
    for item in album_search_results['items']:

        # Make sure it's actually the artist
        if item['artists'][0]['name'] in [artist_name] + additional_artists:
            
            # If it has the minimum number of songs
            if item['total_tracks'] >= min_album_songs:
            
                # If we haven't already chosen the album
                if item['name'] not in chosen_albums.keys():

                    # If it's not an alternate album version
                    if ('edition' not in item['name'].lower()) & ('version' not in item['name'].lower()):

                        # Add to nested dictionary
                        chosen_albums[item['name']] = {'id':item['id'], 'release_date':item['release_date']}

    
    ########### Song IDs ###########
    
    # Collect song IDs from each album
    song_dict = {}
    id_list = []
    for album in chosen_albums:
        
        if verbose==1:
            print(f"Collecting data for {album}...")
        
        # Scrape album tracks info
        album_tracks_info = sp.album_tracks(album_id=chosen_albums[album]['id'], limit=50)

        # Collect song-by-song titles and IDs
        for item in album_tracks_info['items']:
            song_id = item['id']
            song_name = item['name']
            
            id_list.append(song_id)

            song_dict[song_id] = {'artist_name':artist_name, 
                                  'song_name':song_name, 
                                  'album_name':album, 
                                  'album_release_date':chosen_albums[album]['release_date']
                                 }

    # Convert album info to df
    song_dict_df = pd.DataFrame(song_dict).transpose()
    
    
    ########### Song metadata ###########
    
    # Collect all song metadata in 50-song chunks
    song_info = []
    for i in range(0, len(id_list), 50):
        song_info_chunk = sp.audio_features(tracks=id_list[i:i+50])
        song_info.append(song_info_chunk)

    # Flatten chunks into one list
    song_info = [track for chunk in song_info for track in chunk]

    # Convert all metadata features to df
    song_features_df = pd.DataFrame({
        'id':[i['id'] for i in song_info],
        'danceability':[i['danceability'] for i in song_info],
        'energy':[i['energy'] for i in song_info],
        'key':[i['key'] for i in song_info],
        'loudness':[i['loudness'] for i in song_info],
        'mode':[i['mode'] for i in song_info],
        'speechiness':[i['speechiness'] for i in song_info],
        'acousticness':[i['acousticness'] for i in song_info],
        'instrumentalness':[i['instrumentalness'] for i in song_info],
        'liveness':[i['liveness'] for i in song_info],
        'valence':[i['valence'] for i in song_info],
        'tempo':[i['tempo'] for i in song_info],
        'duration_ms':[i['duration_ms'] for i in song_info],
        'time_signature':[i['time_signature'] for i in song_info]
    })
    
    
    ########### Final dataframe ###########
    
    # Full song information df
    full_song_df = pd.merge(song_dict_df, song_features_df, left_index=True, right_on='id')

    # Songs longer than X seconds
    full_song_df = full_song_df[full_song_df.duration_ms >= min_seconds * 1000]
    
    return(full_song_df)