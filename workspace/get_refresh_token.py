"""
Run once locally to generate a refresh token with the correct scopes.
Requires: pip install spotipy python-dotenv
"""
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.environ["SPOTIFY_CLIENT_ID"],
    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
    scope="user-read-recently-played user-top-read",
))

# Trigger auth — browser will open
sp.current_user()

# Print the refresh token
cache = sp.auth_manager.get_cached_token()
print("\n--- REFRESH TOKEN ---")
print(cache["refresh_token"])
print("---------------------")
print("Copy this into your SPOTIFY_REFRESH_TOKEN KV value in Kestra.")
