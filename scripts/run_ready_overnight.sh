#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "${LOCALAI_MODE:-DAY_MODE}" != "NIGHT_MODE" ] && [ "${LOCALAI_MANUAL_RESUME:-false}" != "true" ]; then
  echo "Refusing overnight execution outside NIGHT_MODE unless LOCALAI_MANUAL_RESUME=true." >&2
  echo "Manual command when you mean it: LOCALAI_MODE=NIGHT_MODE bash scripts/run_ready_overnight.sh" >&2
  exit 2
fi

.venv/bin/python -m assistant_core.cli run-ready-overnight
