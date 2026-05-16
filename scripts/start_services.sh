#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI not found. Install Docker Desktop manually, then rerun this script." >&2
  echo "Manual install: brew install --cask docker" >&2
  exit 2
fi

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is not available from this Docker CLI." >&2
  echo "Install Docker Desktop manually, then open it once:" >&2
  echo "  brew install --cask docker" >&2
  exit 2
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable. Open Docker Desktop, wait until it is running, then rerun this script." >&2
  exit 2
fi

"${COMPOSE[@]}" up -d postgres temporal temporal-ui open-webui

if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "Ollama-compatible API is reachable at http://localhost:11434"
else
  echo "Ollama-compatible API is not reachable. Start Ollama manually before model-backed work." >&2
fi

echo "Local service URLs:"
echo "  Open WebUI:  http://localhost:3000"
echo "  Temporal UI: http://localhost:8233"
echo "  Postgres:    localhost:5432"
