#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:0}"
URL="${KLASBOT_KIOSK_URL:-http://127.0.0.1:8000}"

if command -v xset >/dev/null 2>&1; then
  xset s off || true
  xset -dpms || true
  xset s noblank || true
fi

CHROME_BIN=""
for candidate in chromium-browser chromium chromium --no-sandbox; do
  name="${candidate%% *}"
  if command -v "$name" >/dev/null 2>&1; then
    CHROME_BIN="$name"
    break
  fi
done

if [ -z "$CHROME_BIN" ]; then
  echo "Chromium is not installed." >&2
  exit 1
fi

exec "$CHROME_BIN" \
  --kiosk "$URL" \
  --noerrdialogs \
  --disable-infobars \
  --disable-pinch \
  --overscroll-history-navigation=0 \
  --check-for-update-interval=31536000
