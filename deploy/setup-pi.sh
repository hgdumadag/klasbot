#!/usr/bin/env bash
set -euo pipefail

APP_USER="${KLASBOT_USER:-klasbot}"
APP_DIR="${KLASBOT_APP_DIR:-/opt/klasbot}"
DATA_DIR="${KLASBOT_DATA_DIR:-/var/lib/klasbot}"
REPO_URL="${KLASBOT_REPO_URL:-https://github.com/hgdumadag/klasbot.git}"
MODEL="${OLLAMA_MODEL:-gemma4:e2b}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run setup-pi.sh with sudo." >&2
  exit 1
fi

apt-get update
apt-get install -y \
  chromium-browser \
  cups \
  curl \
  git \
  python3 \
  python3-pip \
  python3-venv \
  x11-xserver-utils

if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

mkdir -p "$APP_DIR" "$DATA_DIR"
chown -R "$APP_USER:$APP_USER" "$APP_DIR" "$DATA_DIR"

if [ ! -d "$APP_DIR/.git" ]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
else
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
fi

sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" -m pip install -e "$APP_DIR"

if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

systemctl enable --now cups
systemctl enable --now ollama || true

if command -v ollama >/dev/null 2>&1; then
  sudo -u "$APP_USER" ollama pull "$MODEL" || true
fi

install -m 0644 "$APP_DIR/deploy/klasbot.service" /etc/systemd/system/klasbot.service
install -m 0755 "$APP_DIR/deploy/kiosk.sh" /usr/local/bin/klasbot-kiosk
systemctl daemon-reload
systemctl enable --now klasbot.service

echo "Klasbot installed. Seed an admin with:"
echo "sudo -u $APP_USER KLASBOT_DB_PATH=$DATA_DIR/klasbot.db $APP_DIR/.venv/bin/python $APP_DIR/scripts/seed_admin.py --name Admin --pin 1111"
