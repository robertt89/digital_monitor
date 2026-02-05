#!/usr/bin/env bash
set -euo pipefail

BRANCH=${BRANCH:-main}
REPO_URL=${REPO_URL:-}
WORKDIR=${WORKDIR:-/opt/led-monitor}

if [[ -z "$REPO_URL" ]]; then
  echo "REPO_URL env var is required (e.g. git@github.com:user/repo.git)" >&2
  exit 1
fi

if [[ ! -d "$WORKDIR/.git" ]]; then
  echo "Cloning repository into $WORKDIR"
  rm -rf "$WORKDIR"
  git clone "$REPO_URL" "$WORKDIR"
fi

cd "$WORKDIR"

echo "Switching to $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "Rebuilding containers"
docker compose pull
BRANCH=$BRANCH docker compose up -d --build
