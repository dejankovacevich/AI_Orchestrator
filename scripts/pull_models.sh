#!/usr/bin/env bash
set -euo pipefail

MODELS=(
  "qwen3:30b-a3b"
  "qwen3-coder:30b-a3b"
  "deepseek-r1:8b"
)
LARGE_MODEL="llama3.3:70b"
ALTERNATIVES=(
  "qwen3:32b"
  "qwen3:14b"
  "qwen2.5-coder:32b"
  "deepseek-r1:32b"
  "deepseek-r1:14b"
)

if ! command -v ollama >/dev/null 2>&1; then
  echo "ollama CLI not found. Install/start Ollama manually before pulling models." >&2
  echo "Example manual command after installing Ollama: ollama pull qwen3:14b" >&2
  exit 2
fi

pull_one() {
  local model="$1"
  if ollama pull "$model"; then
    echo "Pulled $model"
  else
    echo "Failed to pull $model; continuing." >&2
  fi
}

for model in "${MODELS[@]}"; do
  pull_one "$model"
done

if [ "${LOCALAI_PULL_LLAMA70B:-false}" = "true" ]; then
  pull_one "$LARGE_MODEL"
else
  echo "Skipping $LARGE_MODEL because it is large."
  echo "To pull it explicitly: LOCALAI_PULL_LLAMA70B=true bash scripts/pull_models.sh"
fi

echo "If any preferred tag failed, try one of these alternatives manually:"
for model in "${ALTERNATIVES[@]}"; do
  echo "  ollama pull $model"
done
