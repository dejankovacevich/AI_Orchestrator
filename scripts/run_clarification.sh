#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$#" -ne 1 ]; then
  echo "Usage: bash scripts/run_clarification.sh <work_packet_id>" >&2
  exit 2
fi

.venv/bin/python -m assistant_core.cli run-clarification "$1"
