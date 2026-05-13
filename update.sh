#!/bin/sh
REPO="$(cd "$(dirname "$0")" && pwd)"
docker run --rm -v "$REPO:/repo" -w /repo alpine/git pull
cd "$REPO"
SHA=$(docker run --rm -v "$REPO:/repo" -w /repo alpine/git rev-parse HEAD)
sudo docker compose build --build-arg FIRSTLIGHT_VERSION="$SHA"
sudo docker compose up -d
