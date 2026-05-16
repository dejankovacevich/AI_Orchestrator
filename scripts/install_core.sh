#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON_BIN="${LOCALAI_PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  for candidate in python3.13 python3.12 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON_BIN" ]; then
  echo "No Python interpreter found. Install Python manually, for example: brew install python@3.13" >&2
  exit 2
fi

echo "Using Python: $($PYTHON_BIN --version)"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip

if ! .venv/bin/python -m pip install \
  temporalio \
  langgraph \
  langchain \
  langchain-ollama \
  litellm \
  pydantic \
  pandas \
  pyyaml \
  python-dotenv \
  'psycopg[binary]' \
  sqlalchemy \
  chromadb \
  streamlit \
  requests \
  rich \
  loguru \
  pytest; then
  echo "Python dependency install failed." >&2
  echo "If this is a Python 3.14 compatibility issue, install a stable interpreter manually:" >&2
  echo "  brew install python@3.13" >&2
  echo "Then rerun:" >&2
  echo "  LOCALAI_PYTHON_BIN=/opt/homebrew/bin/python3.13 bash scripts/install_core.sh" >&2
  exit 2
fi

.venv/bin/python -m assistant_core.cli ensure-folders

echo "Core Python environment and local folder structure are ready."
echo "This script does not install Docker Desktop, Ollama, Homebrew, launchd jobs, or large models."
