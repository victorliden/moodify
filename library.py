import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import os
from typing import Any, Iterator
import json
from genre_to_mood_dict import genre_mood_dict 
from openai_methods import mood_sorter

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

class Track():

    def __init__(self, track : dict, library) -> None:
        
        self.library = library
        self.artists = [artist['name'] for artist in track['artists']]
        self.title = track['name']
        self.album = track['album']["name"]
        self.id = track["id"]
        print(f"Processing {self}")

        artist_ids = [artist['uri'].split(':')[-1] for artist in track['artists']]

        self.genres = set()
        # Batch artist IDs into chunks of 50
        for i in range(0, len(artist_ids), 50):
            batch_ids = artist_ids[i:i + 50]
            retrieved_artists = self.library.sp.artists(batch_ids)['artists']
            for artist in retrieved_artists:
                self.genres.update(artist.get('genres', []))

    # def get_genres(self) -> set[Any]:
    #     track['artists']
    #     artist_ids = [artist['uri'].split(':')[-1] for artist in artists]

    #     genres = set()
    #     # Batch artist IDs into chunks of 50
    #     for i in range(0, len(artist_ids), 50):
    #         batch_ids = artist_ids[i:i + 50]
    #         retrieved_artists = self.library.sp.artists(batch_ids)['artists']
    #         for artist in retrieved_artists:
    #             genres.update(artist.get('genres', []))

    #     return genres
    
    def get_track_dict(self):
        track_data = {
            "title": self.title,
            "artists": self.artists,
            "genres": list(self.genres),
            "album": self.album,
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
                track = Track(item["track"], self).get_track_dict()
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
    
    def _get_all_saved_tracks(self) -> Iterator[Any]:
        offset = 0
        while True:
            result : Any = self.sp.current_user_saved_tracks(offset=offset, limit=50)
            items = result.get("items", [])
            if not items:
                break
            for item in items:
                yield item
            offset += 50
    
    def get_playlists_def(self) -> list[dict[str, list[str]]]:    #temporary - will only work for my one
        print("Dividing genres into moods")
        try:   
            return mood_sorter(list(self.covered_genres))["moods"]
        except Exception as e:
            print(e)
            return [{}]
    
    def split_into_playlists(self, ):
        print("Sorting tracks into playlistst")
        mood_tracks_dict : dict[str, list[dict]] = {}
        playlist_def : list = self.get_playlists_def()

        mood_tracks_dict = {mood["name"]: [] for mood in playlist_def}

        mood_tracks_dict["others"] = []

        for track in self.tracks:
            match = False
            track_genres = set(track["genres"])
            for mood_dict in playlist_def:
                if track_genres & set(mood_dict["genres"]):
                    mood_tracks_dict[mood_dict["name"]].append(track)
                    match = True
            if not match:
                mood_tracks_dict["others"].append(track)

        print("Playlists are made")

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
                if "(Moodify) Liked Songs - " in str(playlist.get("name")) == str("Liked Songs - " + mood):
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

    
