#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_PORT="${FRONTEND_PORT:-3060}"
API_PORT="${API_PORT:-6060}"
HOST="${HOST:-0.0.0.0}"

cd "$ROOT_DIR"

cleanup() {
  echo
  echo "Stopping API and frontend..."
  jobs -p | xargs -r kill
}
trap cleanup EXIT INT TERM

echo "Starting vLLM in background..."
docker compose up -d vllm

echo "Starting API on ${HOST}:${API_PORT}..."
source env/bin/activate
uvicorn backend.app.main:app --reload --host "$HOST" --port "$API_PORT" &

echo "Starting frontend on ${HOST}:${FRONTEND_PORT}..."
cd "$ROOT_DIR/frontend"
npm run dev -- --hostname "$HOST" --port "$FRONTEND_PORT" &

LAN_IP="$(hostname -I | awk '{print $1}')"
echo
echo "InsightCap dev stack is starting."
echo "Frontend: http://${LAN_IP}:${FRONTEND_PORT}"
echo "API:      http://${LAN_IP}:${API_PORT}/health"
echo "vLLM:     http://${LAN_IP}:8060/health"
echo
echo "Press Ctrl+C to stop API and frontend. vLLM stays running; stop it with: docker compose stop vllm"

wait
