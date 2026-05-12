#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${KLASBOT_APP_DIR:-/opt/klasbot}"
APP_USER="${KLASBOT_USER:-klasbot}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run update.sh with sudo." >&2
  exit 1
fi

sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" -m pip install -e "$APP_DIR"
systemctl restart klasbot.service
systemctl --no-pager --full status klasbot.service
