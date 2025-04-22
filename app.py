from flask import Flask, redirect, session, request, render_template, jsonify
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from library import Library
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = [
    "user-library-read",
    "playlist-modify-private",
    "playlist-read-private",
    "playlist-read-collaborative"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    auth_manager = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)
    return redirect(auth_manager.get_authorize_url())

@app.route("/callback")
def callback():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)
    session.clear()
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/generate")

@app.route("/start-generation", methods=["POST"])
def start_generation():
    token_info = session.get("token_info")
    if not token_info:
        return redirect("/login")

    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=SCOPE)

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session["token_info"] = token_info

    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    lib = Library(sp)
    lib.create_library_from_saved_tracks()
    lib.split_into_playlists()
    lib.make_playlists()

    return jsonify({"status": "done"})

@app.route("/generate")
def generate():
    return render_template("loading.html")

@app.route("/result")
def result():
    return render_template("result.html") 

if __name__ == "__main__":
    app.run(debug=True)