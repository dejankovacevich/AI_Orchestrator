#!/usr/bin/env bash
# One-shot synchronous code review for indie hackers / contractors / solo devs.
#
# Usage:
#   bash scripts/review_code.sh path/to/file_or_dir [TITLE] [DESCRIPTION]
#
# What it does:
#   1. Copies the source file (or directory) into ~/LocalAI/inbox/docs/
#   2. Creates a work packet with task_type=code_review
#   3. Submits a canned answer file so readiness goes READY immediately
#   4. Runs the executor synchronously (bypasses Temporal) with
#      --manual-override so it works during the day
#   5. Prints where the review landed (~/LocalAI/output/<date>/01_CODE_REVIEW.md
#      plus a copy in ~/Obsidian/.../02_Work_Packets/)
#
# Requires:
#   - bash scripts/start_services.sh (Postgres up)
#   - brew services start ollama (Ollama up)
#   - at least one of {local-coder, local-main} pulled

set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/review_code.sh <path-to-file-or-dir> [TITLE] [DESCRIPTION]" >&2
  exit 2
fi

SOURCE="$1"
if [ ! -e "$SOURCE" ]; then
  echo "Source path does not exist: $SOURCE" >&2
  exit 2
fi
BASENAME="$(basename "$SOURCE")"
TITLE="${2:-Code review: $BASENAME}"
DESCRIPTION="${3:-Review this code for clarity issues, suggest a refactor that improves testability, and propose three additional test cases. Stay within existing dependencies. Audience: me, then I share with a teammate.}"

INBOX_DIR="$HOME/LocalAI/inbox/docs"
mkdir -p "$INBOX_DIR"
TARGET="$INBOX_DIR/$BASENAME"
cp -r "$SOURCE" "$TARGET"

PYTHON=".venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo ".venv missing. Run: bash scripts/install_core.sh" >&2
  exit 2
fi

echo "Creating packet (task_type=code_review)..."
PACKET_JSON="$($PYTHON -m assistant_core.cli create-work-packet \
  --task-type code_review \
  "$TITLE" "$DESCRIPTION")"
PACKET_ID="$($PYTHON -c "import json,sys; print(json.loads(sys.argv[1])['work_packet_id'])" "$PACKET_JSON")"

echo "Packet id: $PACKET_ID"

ANSWERS="$(mktemp).md"
cat > "$ANSWERS" <<EOF
Outputs: 01_CODE_REVIEW.md in markdown.
Sources: $TARGET
Cloud: do not use cloud fallback.
Audience: me, then I share with a teammate.
Assumptions: stay within existing dependency set; do not propose new libraries.
Quality: optimize for actionability. Each suggestion applyable in under 10 minutes.
Stop conditions: stop if the file references missing context.
Success: I can apply the suggestions today.
EOF

echo "Submitting answers and rescoring readiness..."
$PYTHON -m assistant_core.cli answer-questions "$PACKET_ID" "$ANSWERS" > /dev/null

echo "Running execution (synchronous, --manual-override)..."
$PYTHON -m assistant_core.cli run-packet-execution "$PACKET_ID" --manual-override

echo
echo "Done. Check the latest output directory under ~/LocalAI/output/$(date +%Y-%m-%d)/"
echo "Vault copy at: ~/Obsidian/LocalAI-ChiefOfStaff/02_Work_Packets/"
