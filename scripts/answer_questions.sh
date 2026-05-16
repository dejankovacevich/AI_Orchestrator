#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$#" -ne 2 ]; then
  echo "Usage: bash scripts/answer_questions.sh <work_packet_id> <answers.md>" >&2
  exit 2
fi

.venv/bin/python -m assistant_core.cli answer-questions "$1" "$2"
