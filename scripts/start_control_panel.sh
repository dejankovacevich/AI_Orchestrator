#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -x .venv/bin/streamlit ]; then
  echo "Streamlit is not installed in .venv. Run: bash scripts/install_core.sh" >&2
  exit 2
fi

export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

exec .venv/bin/streamlit run app/control_panel.py --server.address 127.0.0.1 --server.port 8501
