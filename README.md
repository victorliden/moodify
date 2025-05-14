# MOODIFY 🎵
MOODIFY is a web app that reads your saved songs on Spotify, analyzes their genres to infer moods, and creates playlists grouped by mood directly in your Spotify account.

## 🔧 Setup
To use the app, you’ll need to create a .env file with your Spotify API credentials:

SPOTIPY_CLIENT_ID=your_client_id, 
SPOTIPY_CLIENT_SECRET=your_client_secret, 
SPOTIPY_REDIRECT_URI= for example: http://127.0.0.1:5000/callback (local),
FLASK_SECRET_KEY=some_random_secret_key.

Make sure to register your app on Spotify and add the redirect URI to the list of allowed redirect URIs in your app settings.

## ▶️ Running the app
Install dependencies:

pip install -r requirements.txt

Start the Flask server:

flask run

Open your browser and go to your url
