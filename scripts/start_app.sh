#!/usr/bin/env bash
# Launch the FastAPI dashboard application.
set -euo pipefail

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-8080}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"
exec python3 -m uvicorn server.app:app --host "$APP_HOST" --port "$APP_PORT"
