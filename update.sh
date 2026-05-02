#!/bin/sh
REPO="$(cd "$(dirname "$0")" && pwd)"
docker run --rm -v "$REPO:/repo" -w /repo alpine/git pull
cd "$REPO"
sudo docker compose build
sudo docker compose up -d
