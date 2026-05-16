#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/python ]; then
  echo ".venv missing. Run: bash scripts/install_core.sh" >&2
  exit 2
fi

exec .venv/bin/python -m assistant_core.temporal_app.worker
