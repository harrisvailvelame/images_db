#!/usr/bin/env bash
set -u

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_DIR="$BASE_DIR/staging"

mkdir -p "$STAGING_DIR"

if ! command -v inotifywait >/dev/null 2>&1; then
  echo "inotifywait was not found. Install inotify-tools first." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found." >&2
  exit 1
fi

echo "Watching $STAGING_DIR for incoming assets..."

while true; do
  inotifywait -qq -e close_write -e moved_to -e create "$STAGING_DIR"
  sleep 1

  if python3 "$BASE_DIR/website_upload_pics.py" --consume --push; then
    echo "Ingestion cycle completed."
  else
    echo "Ingestion cycle failed; watcher will continue." >&2
  fi
done
