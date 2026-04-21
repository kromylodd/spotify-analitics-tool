print("Script started", flush=True)
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os, json
from datetime import datetime, timezone
from google.cloud import storage

load_dotenv()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-read-recently-played"
))

# Fetch
print("Fetching recently played...", flush=True)
results = sp.current_user_recently_played(limit=50)

tracks = []
seen = set()

for item in results["items"]:
    played_at = item["played_at"]
    if played_at in seen:
        continue
    seen.add(played_at)

    track = item["track"]
    tracks.append({
        "played_at": played_at,
        "track_id": track["id"],
        "track_name": track["name"],
        "artist_id": track["artists"][0]["id"],
        "artist_name": track["artists"][0]["name"],
        "album_name": track["album"]["name"],
        "duration_ms": track["duration_ms"],
        "explicit": track["explicit"]
    })

print(f"Fetched {len(tracks)} tracks", flush=True)

# Upload to GCS
raw_payload = {
    "ingested_at": datetime.now(timezone.utc).isoformat(),
    "track_count": len(tracks),
    "tracks": tracks
}

now = datetime.now(timezone.utc)
blob_path = f"raw/{now.strftime('%Y/%m/%d/%H_%M')}.json"

client = storage.Client()
bucket = client.bucket(os.getenv("GCS_BUCKET_NAME"))
blob = bucket.blob(blob_path)
blob.upload_from_string(
    json.dumps(raw_payload, indent=2),
    content_type="application/json"
)

print(f"Uploaded {len(tracks)} tracks to gs://{os.getenv('GCS_BUCKET_NAME')}/{blob_path}", flush=True)