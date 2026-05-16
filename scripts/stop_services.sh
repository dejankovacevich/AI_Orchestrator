#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose not found; nothing to stop through Docker Compose." >&2
  exit 0
fi

"${COMPOSE[@]}" stop
echo "Services stopped. Volumes were not deleted."
