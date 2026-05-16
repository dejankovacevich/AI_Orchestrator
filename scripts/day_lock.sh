#!/usr/bin/env bash
# Remove the day-unlock sentinel file so the strict DAY_MODE policy is
# back in effect. If LOCALAI_DAY_UNLOCK is also set in the current shell,
# this script will tell you so you can `unset` it.
#
# Override the state directory with LOCALAI_STATE_DIR.

set -euo pipefail

cd "$(dirname "$0")/.."

STATE_DIR="${LOCALAI_STATE_DIR:-$HOME/LocalAI/state}"
FLAG="$STATE_DIR/day_unlock.flag"

if [ -f "$FLAG" ]; then
  rm "$FLAG"
  echo "Day unlock REMOVED. Strict DAY_MODE policy is back in effect."
else
  echo "Day unlock was not active. No flag file to remove."
fi

if [ -n "${LOCALAI_DAY_UNLOCK:-}" ]; then
  echo
  echo "WARNING: LOCALAI_DAY_UNLOCK='$LOCALAI_DAY_UNLOCK' is set in this shell."
  echo "  The env var override is still active for processes started from this shell."
  echo "  Clear it with: unset LOCALAI_DAY_UNLOCK"
fi
