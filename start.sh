#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BACKEND_PORT=${BACKEND_PORT:-8327}
FRONTEND_PORT=${FRONTEND_PORT:-3327}
PYTHON=${BACKEND_PYTHON:-"$ROOT/backend/.venv313/bin/python"}
if [ ! -x "$PYTHON" ]; then echo "Install backend dependencies first. See README.md." >&2; exit 1; fi
if [ ! -d "$ROOT/frontend/node_modules" ]; then echo "Run npm ci in frontend first." >&2; exit 1; fi
(cd "$ROOT/backend" && exec "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT") &
backend_pid=$!
cleanup(){ kill "$backend_pid" "${frontend_pid:-$backend_pid}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
(cd "$ROOT/frontend" && BACKEND_URL="http://127.0.0.1:$BACKEND_PORT" NEXT_TELEMETRY_DISABLED=1 exec npm run dev -- --hostname 127.0.0.1 --port "$FRONTEND_PORT") &
frontend_pid=$!
wait "$backend_pid" "$frontend_pid"
