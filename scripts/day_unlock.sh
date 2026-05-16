#!/usr/bin/env bash
# Create the day-unlock sentinel file so the safety layer treats DAY_MODE
# the same as manual_override=True. All local-* model groups become callable
# until you remove the flag (or it is removed by day_lock.sh).
#
# Usage:
#   bash scripts/day_unlock.sh
#   bash scripts/day_unlock.sh "Investigating overnight output during the day"
#
# Override the state directory with LOCALAI_STATE_DIR.

set -euo pipefail

cd "$(dirname "$0")/.."

STATE_DIR="${LOCALAI_STATE_DIR:-$HOME/LocalAI/state}"
FLAG="$STATE_DIR/day_unlock.flag"
REASON="${*:-no reason given}"

mkdir -p "$STATE_DIR"

cat > "$FLAG" <<EOF
unlocked_at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
unlocked_by: $USER@$(hostname)
reason: $REASON
EOF

echo "Day unlock ACTIVE."
echo "Flag file: $FLAG"
echo "Contents:"
sed 's/^/  /' "$FLAG"
echo
echo "Local-* model groups can now run in DAY_MODE."
echo "Lock again with: bash scripts/day_lock.sh"
