#!/usr/bin/env bash
set -euo pipefail
APP_NAME="paper-scitech-landscape"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="${INSTALL_DIR:-$HOME/$APP_NAME}"
PORT="${PORT:-8012}"
SPARK_BASE_URL="${SPARK_BASE_URL:-http://127.0.0.1:8000/v1}"
SPARK_MODEL="${SPARK_MODEL:-auto}"

echo "Installing to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -a "$SRC_DIR"/. "$INSTALL_DIR"/
cd "$INSTALL_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
cat > .env <<EOF
SPARK_BASE_URL=$SPARK_BASE_URL
SPARK_MODEL=$SPARK_MODEL
SPARK_API_KEY=${SPARK_API_KEY:-}
SPARK_TIMEOUT=120
HOST=0.0.0.0
PORT=$PORT
EOF

SERVICE="$HOME/.config/systemd/user/$APP_NAME.service"
mkdir -p "$(dirname "$SERVICE")"
cat > "$SERVICE" <<EOF
[Unit]
Description=Science Technology Landscape on DGX Spark
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/run.sh
Restart=on-failure
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now "$APP_NAME.service"
sleep 1
systemctl --user --no-pager --full status "$APP_NAME.service" || true
echo
echo "Health: http://127.0.0.1:$PORT/api/health"
echo "App:    http://127.0.0.1:$PORT/"
echo "LAN:    http://<SPARK-IP>:$PORT/"
