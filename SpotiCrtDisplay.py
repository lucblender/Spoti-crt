import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep

scope = "user-library-read, user-read-currently-playing, user-read-playback-state"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

class Track():
    def __init__(self, is_playing, progress_ms, duration_ms, album_uri, title, album_name, artists_name):
        self.is_playing = is_playing
        self.progress_ms = progress_ms
        self.duration_ms = duration_ms
        self.album_uri = album_uri
        self.title = title
        self.album_name = album_name
        self.artists_name = artists_name
        

def get_current_track_info():
    current_track = sp.current_playback()
    is_playing = current_track['is_playing']
    progress_ms = current_track['progress_ms']
    duration_ms = current_track['item']['duration_ms']
    album_uri = current_track['item']['album']['images'][0]['url']
    title = current_track['item']['name']
    album_name = current_track['item']['album']['name']
    artists_name = []
    for artist in current_track['item']['album']['artists']:
        artists_name.append(artist['name'])
    
    return Track(is_playing, progress_ms, duration_ms, album_uri, title, album_name, artists_name)



