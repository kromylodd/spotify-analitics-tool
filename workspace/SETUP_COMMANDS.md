# Spotify Analytics Tool — Restore Commands

## 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/spotify-analitics-tool.git
cd spotify-analitics-tool
```

---

## 2. Install Python dependencies
```bash
pip install spotipy google-cloud-storage python-dotenv
```

Verify spotipy installed:
```bash
python -c "import spotipy; print(spotipy.__version__)"
```

---

## 3. Recreate .env file
Create a `.env` file in the project root with:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/gcp-key.json
```

---

## 4. Re-upload GCP service account key
Place your `gcp-key.json` in the project root (do NOT commit this).
Make sure `.gitignore` has:
```
.env
.cache
gcp-key.json
```

---

## 5. Authenticate GCP locally
```bash
gcloud auth application-default login
```

Or if using a service account key directly, set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-key.json
```

---

## 6. Fix script permissions
```bash
chmod +x python_ingest.py
```

---

## 7. Select Python interpreter (VS Code)
`Ctrl+Shift+P` → "Python: Select Interpreter" → pick system Python or venv

Add to VS Code settings JSON (`Ctrl+Shift+P` → "Open User Settings JSON"):
```json
"python.terminal.useEnvFile": true
```

---

## 8. First run — Spotify OAuth
Run once locally to generate the `.cache` token file:
```bash
python python_ingest.py
```
Browser will open for Spotify authorization. After that, token is cached and auto-refreshed.

---

## 9. Docker setup
```bash
# Build image
docker build -t spotify-ingest .

# Run via docker-compose
docker-compose up
```

> Note: `.cache` must exist before running in Docker (step 8 handles this).
> The volume mount in docker-compose.yml picks it up automatically.

---

## Quick reference — run the pipeline
```bash
python python_ingest.py
```
Or via Docker:
```bash
docker-compose up
```
