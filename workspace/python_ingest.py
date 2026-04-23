import os
import json
import base64
import logging
import requests
from datetime import datetime, timezone
from google.cloud import storage, secretmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config — all pulled from env vars set by Kestra
# ---------------------------------------------------------------------------
CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["SPOTIFY_REFRESH_TOKEN"]
BUCKET_NAME = os.environ["GCS_BUCKET"]
LAST_TS_BLOB = "state/last_played_at.txt"  # stores cursor between runs


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def get_access_token() -> str:
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}"},
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ValueError(f"No access_token in response: {resp.json()}")
    log.info("Access token refreshed successfully")
    return token


# ---------------------------------------------------------------------------
# State — read/write cursor to GCS so we don't re-ingest on overlap
# ---------------------------------------------------------------------------
def read_last_timestamp(bucket) -> int | None:
    blob = bucket.blob(LAST_TS_BLOB)
    if not blob.exists():
        log.info("No cursor found — fetching full 50-track window")
        return None
    ts = int(blob.download_as_text().strip())
    log.info(f"Cursor: fetching tracks after {ts} ({datetime.fromtimestamp(ts/1000, tz=timezone.utc).isoformat()})")
    return ts


def write_last_timestamp(bucket, ts_ms: int):
    bucket.blob(LAST_TS_BLOB).upload_from_string(str(ts_ms))
    log.info(f"Cursor updated to {ts_ms}")


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------
def fetch_recently_played(access_token: str, after_ts: int | None) -> dict:
    params = {"limit": 50}
    if after_ts:
        params["after"] = after_ts

    resp = requests.get(
        "https://api.spotify.com/v1/me/recently-played",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get("items", [])
    log.info(f"Fetched {len(items)} tracks")
    return data


def fetch_top_tracks(access_token: str) -> dict:
    """Supplemental — rolling 4-week window, resilient to ingestion gaps."""
    resp = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": 50, "time_range": "short_term"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Write to GCS
# ---------------------------------------------------------------------------
def write_to_gcs(bucket, data: dict, prefix: str) -> str:
    now = datetime.now(timezone.utc)
    path = f"raw/{prefix}/{now:%Y/%m/%d}/{now:%H_%M_%S}.json"
    blob = bucket.blob(path)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False),
        content_type="application/json",
    )
    log.info(f"Written to gs://{BUCKET_NAME}/{path}")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    token = get_access_token()

    # --- Recently played (incremental via cursor) ---
    last_ts = read_last_timestamp(bucket)
    recent_data = fetch_recently_played(token, after_ts=last_ts)

    items = recent_data.get("items", [])
    if items:
        recent_path = write_to_gcs(bucket, recent_data, "recently_played")

        # Update cursor to the most recent played_at timestamp
        latest_ts_ms = max(
            int(datetime.fromisoformat(item["played_at"].replace("Z", "+00:00")).timestamp() * 1000)
            for item in items
        )
        write_last_timestamp(bucket, latest_ts_ms)
    else:
        log.info("No new tracks since last run — skipping write")
        recent_path = None

    # --- Top tracks (full snapshot each run) ---
    top_data = fetch_top_tracks(token)
    top_path = write_to_gcs(bucket, top_data, "top_tracks")

    # Kestra output — downstream tasks can reference these paths
    output = {
        "recently_played_path": recent_path,
        "top_tracks_path": top_path,
        "tracks_ingested": len(items),
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(f"::{json.dumps({'outputs': output})}")


if __name__ == "__main__":
    main()
