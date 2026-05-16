#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose ps
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose ps
else
  echo "Docker Compose not found"
fi

echo "URLs:"
echo "  Ollama:       http://localhost:11434"
echo "  Open WebUI:   http://localhost:3000"
echo "  LiteLLM:      http://localhost:4000"
echo "  Temporal:     localhost:7233"
echo "  Temporal UI:  http://localhost:8233"
echo "  Postgres:     localhost:5432"
echo "  Control UI:   http://localhost:8501"
