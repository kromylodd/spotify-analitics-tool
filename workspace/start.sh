#!/bin/bash
source .env

GCP_KEY_B64=$(base64 -w 0 gcp-key.json)

cat > .env.kestra << EOF
SECRET_SPOTIFY_CLIENT_ID=$(echo -n "$SPOTIFY_CLIENT_ID" | base64 -w 0)
SECRET_SPOTIFY_CLIENT_SECRET=$(echo -n "$SPOTIFY_CLIENT_SECRET" | base64 -w 0)
SECRET_SPOTIFY_REFRESH_TOKEN=$(echo -n "$SPOTIFY_REFRESH_TOKEN" | base64 -w 0)
SECRET_GCS_BUCKET=$(echo -n "$GCS_BUCKET" | base64 -w 0)
SECRET_GCP_KEY_BASE64=$(cat gcp-key.json)
EOF

docker compose down
docker compose up -d