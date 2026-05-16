#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$#" -ne 2 ]; then
  echo "Usage: bash scripts/create_work_packet.sh \"Title\" \"Description\"" >&2
  exit 2
fi

if [ ! -x .venv/bin/python ]; then
  echo ".venv missing. Run: bash scripts/install_core.sh" >&2
  exit 2
fi

.venv/bin/python -m assistant_core.cli create-work-packet "$1" "$2"
