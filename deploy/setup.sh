#!/usr/bin/env bash
# Cai DRL Watcher thanh dich vu systemd tren may chu Linux (Ubuntu/Debian).
# Chay:  bash setup.sh
# Can co drl_watch.py (va nen co config.json) o cung thu muc voi file nay.
set -e

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$HOME/drl"
USER_NAME="$(id -un)"
PY="$(command -v python3 || true)"

if [ -z "$PY" ]; then
  echo "Khong tim thay python3. Cai bang: sudo apt update && sudo apt install -y python3"
  exit 1
fi

if [ ! -f "$SRC_DIR/drl_watch.py" ]; then
  echo "Khong thay drl_watch.py o $SRC_DIR. Hay dat drl_watch.py canh setup.sh."
  exit 1
fi

echo ">> Cai vao $APP_DIR (python: $PY, user: $USER_NAME)"
mkdir -p "$APP_DIR"
cp "$SRC_DIR/drl_watch.py" "$APP_DIR/drl_watch.py"
[ -f "$SRC_DIR/config.json" ] && cp -n "$SRC_DIR/config.json" "$APP_DIR/config.json" || true

if [ ! -f "$APP_DIR/config.json" ]; then
  echo ">> Chua co config.json -> tao file mau. Hay sua lai sau (hoac dung /token qua Telegram)."
  cat > "$APP_DIR/config.json" <<JSON
{
  "session_token": "",
  "username": "",
  "telegram_bot_token": "DAN_TOKEN_BOT",
  "telegram_chat_id": "DAN_CHAT_ID",
  "poll_seconds": 30,
  "notify_states": ["OPEN", "SOON"],
  "notify_new_any_state": true
}
JSON
fi

SERVICE=/etc/systemd/system/drl-watch.service
echo ">> Tao dich vu systemd: $SERVICE (can sudo)"
sudo tee "$SERVICE" >/dev/null <<UNIT
[Unit]
Description=DRL Watcher - theo doi su kien dat ve ctsv.hust.edu.vn
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
echo " DA CAI XONG. Bot chay nen + tu bat khi reboot."
echo
echo " Xem tinh trang : systemctl status drl-watch"
echo " Xem log song   : journalctl -u drl-watch -f"
echo " Khoi dong lai  : sudo systemctl restart drl-watch"
echo " Dung han       : sudo systemctl disable --now drl-watch"
echo "===================================================="
sleep 1
systemctl --no-pager --full status drl-watch.service || true
