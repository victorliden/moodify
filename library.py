import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import os
from typing import Any
import json
from genre_to_mood_dict import genre_mood_dict 

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

class Track():

    def __init__(self, track : dict, library) -> None:
        self.library = library
        self.track = track
        self.artists = [artist['name'] for artist in track['artists']]
        self.title = track['name']
        self.album = track['album']
        self.genres = self.get_genres()
        self.id = track["id"]
        
        
        print(f"Processing {self}")

    def get_genres(self) -> set[Any]:    #Could check if artist already is in library to reduce api-calls
        artists = self.track['artists']

        genres = set()
        for artist in artists:
            retreived_artist : Any = self.library.sp.artist(artist['uri'])
            artist_genres = retreived_artist['genres']
            for genre in artist_genres:
                genres.add(genre)
        return genres
    
    def get_track_dict(self):
        track_data = {
            "title": self.title,
            "artists": self.artists,
            "genres": list(self.genres),
            "album": self.album['name'],
            "id": self.id}
        return track_data
    
    def __str__(self) -> str:
        return f"\"{self.title}\" by {self.artists}"
    

class Library():
    """
    Class object containing a collected library. Attributeds
    """

    def __init__(self, sp : Spotify) -> None:
    
        self.sp = sp

        user_info = self.sp.me()
        assert user_info is not None
        self.user_id = user_info["id"]

        self.processed_artists = {}

        self.covered_genres = dict()

        self.tracks : list[dict] = list()

        self.sorted_genres = []

        self.playlists = {}

    def create_library_from_saved_tracks(self):
        i=0
        for item in self._get_all_saved_tracks():
            try:
                track = Track(item["track"], self)
                track = track.get_track_dict()
                self.tracks.append(track)
                for genre in track["genres"]:
                    self.covered_genres[genre] = self.covered_genres.get(genre, 0) + 1
                i += 1
            except Exception as e:
                print(f"failed on track {i+1}: {e}")
        self._save_library("tracks.json")
        print(f"A library of {i} tracks have been made")

        
    def _save_library(self, filepath):
        track_data = list(self.tracks)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(track_data, f, indent=4)

        print("saving library")

    def load_library(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            self.tracks = json.load(f)
        print("Library has been loaded")

    def sort_genres(self):  
        list_genres = list()
        for genre, count in self.covered_genres.items():
            list_genres.append((count, genre))
        list_genres.sort(reverse=True)
        self.sorted_genres = list_genres
        return list_genres
    
    def _get_all_saved_tracks(self,) -> list[Any]:
        all_tracks = []
        offset = 0

        while True:
            result : Any = self.sp.current_user_saved_tracks(offset=offset, limit=50)
            items = result.get("items")

            if not items:
                break

            all_tracks.extend(items)
            offset += 50

        return all_tracks
    
    def get_playlists_def(self) -> dict[str, list[str]]:     #temporary - will only work for my one
        return genre_mood_dict
    
    def split_into_playlists(self, ):

        mood_tracks_dict : dict[str, list[dict]] = {}
        playlist_def = self.get_playlists_def()

        for mood in playlist_def:
            mood_tracks_dict[mood] = []

        mood_tracks_dict["others"] = []

        for track in self.tracks:
            match = False
            track_genres = set(track["genres"])
            for mood, genres_in_mood in playlist_def.items():
                if track_genres & set(genres_in_mood):
                    mood_tracks_dict[mood].append(track)
                    match = True
            if not match:
                mood_tracks_dict["others"].append(track)


        #testing
        with open("mood_playlists.txt", "w", encoding="utf-8") as f:
            for mood, tracks in mood_tracks_dict.items():
                f.write(f"{mood.upper()} PLAYLIST\n")
                f.write("-" * 30 + "\n")
                for track in tracks:
                    f.write(f"{track['title']} - {track['artists']}\n")
                f.write("\n\n")

        print("Tracks have been split into 5 playlists")

        self.playlists = mood_tracks_dict

        return mood_tracks_dict
    
    def retreive_user_playlists(self):    
        playlists = []
        limit = 50
        offset = 0

        while True:

            result : Any = self.sp.user_playlists(self.user_id, limit=limit, offset = offset)
            items = result.get("items")

            if not items:
                break

            playlists.extend(items)
            offset += 50
        return playlists

    
    def make_playlists(self):
        "making playlists"
        user_playlists = self.retreive_user_playlists()

        for mood in self.playlists:
            tracks = self.playlists[mood]
            track_ids = [track["id"] for track in tracks if track["id"]]
            playlist_created = False

            for playlist in user_playlists:
                if str(playlist.get("name")) == str("Liked Songs - " + mood):
                    for i in range(0, len(track_ids), 100):
                        chunk = track_ids[i:i+100]
                        if i == 0:
                            self.sp.playlist_replace_items(playlist["id"], items=chunk)
                        else:
                            self.sp.playlist_add_items(playlist["id"], items=chunk)
                    playlist_created = True

            if not playlist_created:
                playlist : Any = self.sp.user_playlist_create(user= self.user_id, 
                                                              name = "Liked Songs - " + mood, 
                                                              public = False, 
                                                              description=f"{self.user_id}\'s liked songs matching the mood: {mood}")
                for i in range(0, len(track_ids), 100):
                    chunk = track_ids[i:i+100]
                    self.sp.playlist_add_items(playlist["id"], items=chunk)

    
