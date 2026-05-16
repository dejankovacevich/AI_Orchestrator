#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

bash -n scripts/*.sh

PYTHON="${LOCALAI_TEST_PYTHON:-.venv/bin/python}"
if [ ! -x "$PYTHON" ]; then
  PYTHON="python3"
fi

"$PYTHON" - <<'PY'
from pathlib import Path
import py_compile

for path in sorted(Path(".").rglob("*.py")):
    if ".venv" in path.parts:
        continue
    py_compile.compile(str(path), doraise=True)
print("Python compilation passed")
PY

"$PYTHON" -m pytest

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  docker compose config >/dev/null
  echo "docker compose config passed"
elif command -v docker-compose >/dev/null 2>&1; then
  docker-compose config >/dev/null
  echo "docker-compose config passed"
else
  echo "Docker Compose not found; skipping docker compose config"
  echo "Install Docker Desktop manually when ready: brew install --cask docker"
fi
