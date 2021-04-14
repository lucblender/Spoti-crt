import spotipy
from spotipy.oauth2 import SpotifyOAuth
from time import sleep



class SpotifyTrack():
    def __init__(self, is_playing, progress_ms, duration_ms, album_uri, title, album_name, artists_name):
        self.is_playing = is_playing
        self.progress = self.ms_to_min_sec(progress_ms)
        self.duration = self.ms_to_min_sec(duration_ms)
        self.progress_ms = progress_ms
        self.duration_ms = duration_ms
        if(duration_ms != 0 and progress_ms != 0):
            self.duration_percent = int((progress_ms/duration_ms)*100)
        else:
            self.duration_percent = 0
        self.album_uri = album_uri
        self.title = title
        self.album_name = album_name
        self.artists_name = artists_name
        
    def ms_to_min_sec(self, duration_ms):
        millis = int(duration_ms)
        seconds=int(millis/1000)%60
        minutes=int(millis/(1000*60))
        return ("%02d:%02d" % (minutes, seconds))
        
class SpotifyReader():
    def __init__(self):
        scope = "user-library-read, user-read-currently-playing, user-read-playback-state"

        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope), requests_timeout=10)
        

    def get_current_track_info(self):
        current_track = self.sp.current_playback()
        
        if current_track == None: #in the case there is 
            return None            
                    
        try:
            album_uri = current_track['item']['album']['images'][0]['url']
            title = current_track['item']['name']
            album_name = current_track['item']['album']['name']
        except:
            print("Couldn't get an info from a track!")
            return None 
            
        is_playing = current_track['is_playing']
        try:
            progress_ms = current_track['progress_ms']
        except:
            progress_ms = 0   
        try:
            duration_ms = current_track['item']['duration_ms']
        except:
            duration_ms = 0
        
       
        artists_name = []
        for artist in current_track['item']['album']['artists']:
            artists_name.append(artist['name'])
        
        return SpotifyTrack(is_playing, progress_ms, duration_ms, album_uri, title, album_name, artists_name)



