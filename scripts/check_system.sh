#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

section() {
  printf '\n== %s ==\n' "$1"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

port_status() {
  local port="$1"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf 'port %-5s in use\n' "$port"
    lsof -nP -iTCP:"$port" -sTCP:LISTEN | sed 's/^/  /'
  else
    printf 'port %-5s free\n' "$port"
  fi
}

section "macOS"
sw_vers || true

section "Hardware"
system_profiler SPHardwareDataType | awk '/Model Name|Chip|Memory|Total Number of Cores/ {print}'

section "Disk"
df -h "$PWD" "$HOME" || true

section "Python"
python3 --version || true
if [ -x ".venv/bin/python" ]; then
  .venv/bin/python --version
else
  echo ".venv not found"
fi

section "Homebrew"
if have brew; then
  brew --version | head -n 1
else
  echo "Homebrew not found"
fi

section "Docker"
if have docker; then
  docker --version
  docker info --format 'Docker server: {{.ServerVersion}}' 2>/dev/null || echo "Docker CLI found but daemon is not reachable"
else
  echo "Docker CLI not found"
fi

section "Ollama"
if have ollama; then
  ollama --version || true
  ollama list || true
else
  echo "ollama CLI not found"
fi
if curl -fsS http://localhost:11434/api/tags >/tmp/localai_ollama_tags.json 2>/dev/null; then
  echo "Ollama-compatible API is responding on localhost:11434"
  cat /tmp/localai_ollama_tags.json
  rm -f /tmp/localai_ollama_tags.json
else
  echo "No Ollama-compatible API response on localhost:11434"
fi

section "Ports"
for port in 11434 3000 4000 5432 7233 8233 8501; do
  port_status "$port"
done

section "Containers"
if have docker; then
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || true
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^localai-postgres$' && echo "Postgres container running" || echo "Postgres container not running"
  docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^localai-temporal$' && echo "Temporal container running" || echo "Temporal container not running"
else
  echo "Docker unavailable; container status skipped"
fi
