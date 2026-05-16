#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f config/litellm.yaml ]; then
  cp config/litellm.yaml.example config/litellm.yaml
  echo "Created config/litellm.yaml from example."
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ANTHROPIC_API_KEY is missing. Local-only LiteLLM usage can continue; cloud-claude-opus will fail if called."
fi

if [ ! -x .venv/bin/litellm ]; then
  echo "LiteLLM is not installed in .venv. Run: bash scripts/install_core.sh" >&2
  exit 2
fi

exec .venv/bin/litellm --config config/litellm.yaml --host 127.0.0.1 --port 4000
