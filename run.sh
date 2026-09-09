#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8012}"
exec .venv/bin/python -m uvicorn server:app --host "$HOST" --port "$PORT"
