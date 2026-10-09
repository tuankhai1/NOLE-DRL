#!/usr/bin/env bash
# Install DRL Watcher as a systemd service on a Linux server (Ubuntu/Debian).
# Run:  bash setup.sh
# Requires drl_watch.py (and ideally config.json) in the same folder as this file.
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/drl"
USER_NAME="$(id -un)"
PY="$(command -v python3 || true)"

if [ -z "$PY" ]; then
  echo "python3 not found. Install it with: sudo apt update && sudo apt install -y python3"
  exit 1
fi

if [ ! -f "$SRC_DIR/drl_watch.py" ]; then
  echo "drl_watch.py not found in $SRC_DIR. Put drl_watch.py next to setup.sh."
  exit 1
fi

echo ">> Installing into $APP_DIR (python: $PY, user: $USER_NAME)"
mkdir -p "$APP_DIR"
cp "$SRC_DIR/drl_watch.py" "$APP_DIR/drl_watch.py"
[ -f "$SRC_DIR/config.json" ] && cp -n "$SRC_DIR/config.json" "$APP_DIR/config.json" || true

if [ ! -f "$APP_DIR/config.json" ]; then
  echo ">> No config.json -> creating a template. Edit it later (or use /token via Telegram)."
  cat > "$APP_DIR/config.json" <<JSON
{
  "session_token": "",
  "username": "",
  "telegram_bot_token": "PASTE_BOT_TOKEN",
  "telegram_chat_id": "PASTE_CHAT_ID",
  "poll_seconds": 30,
  "notify_states": ["OPEN", "SOON"],
  "notify_new_any_state": true
}
JSON
fi

SERVICE=/etc/systemd/system/drl-watch.service
echo ">> Creating systemd service: $SERVICE (needs sudo)"
sudo tee "$SERVICE" >/dev/null <<UNIT
[Unit]
Description=DRL Watcher - monitors ticket events on ctsv.hust.edu.vn
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$PY $APP_DIR/drl_watch.py run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now drl-watch.service

echo
echo "===================================================="
echo " DONE. The bot runs in the background and starts on reboot."
echo
echo " Status      : systemctl status drl-watch"
echo " Live logs   : journalctl -u drl-watch -f"
echo " Restart     : sudo systemctl restart drl-watch"
echo " Stop/disable: sudo systemctl disable --now drl-watch"
echo "===================================================="
sleep 1
systemctl --no-pager --full status drl-watch.service || true
