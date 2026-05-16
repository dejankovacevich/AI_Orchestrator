#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT_PLIST="launchd/com.localai.orchestrator.nightly.plist"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/com.localai.orchestrator.nightly.plist"
PROJECT_DIR="$PWD"

# Read night_mode_start ("HH:MM") from config so the plist matches the user's
# configured schedule. Falls back to 01:30 if config is missing or malformed.
NIGHT_START="$(
  python3 - <<'PY' 2>/dev/null || echo "01:30"
from pathlib import Path
import yaml
data = yaml.safe_load(Path("config/assistant.yaml").read_text(encoding="utf-8")) or {}
value = data.get("night_mode_start", "01:30")
if not (isinstance(value, str) and len(value) == 5 and value[2] == ":"):
    value = "01:30"
print(value)
PY
)"
NIGHT_HOUR="${NIGHT_START%%:*}"
NIGHT_MINUTE="${NIGHT_START##*:}"
# Strip any leading zero so launchd's integer parser is happy.
NIGHT_HOUR="${NIGHT_HOUR#0}"; NIGHT_HOUR="${NIGHT_HOUR:-0}"
NIGHT_MINUTE="${NIGHT_MINUTE#0}"; NIGHT_MINUTE="${NIGHT_MINUTE:-0}"

mkdir -p launchd

cat > "$PROJECT_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.localai.orchestrator.nightly</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$PROJECT_DIR/scripts/run_ready_overnight.sh</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$PROJECT_DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>LOCALAI_MODE</key>
    <string>NIGHT_MODE</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>$NIGHT_HOUR</integer>
    <key>Minute</key>
    <integer>$NIGHT_MINUTE</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$HOME/LocalAI/logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/LocalAI/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

echo "Created project-local plist at $PROJECT_PLIST"
echo "Scheduled for $(printf '%02d:%02d' "$NIGHT_HOUR" "$NIGHT_MINUTE") (from night_mode_start in config/assistant.yaml)"

if [ "${LOCALAI_WRITE_LAUNCHD:-false}" = "true" ]; then
  install -m 644 "$PROJECT_PLIST" "$LAUNCHD_PLIST"
  echo "Copied plist to $LAUNCHD_PLIST"
  echo "Not loaded. Review it first, then load manually with:"
  echo "  launchctl load \"$LAUNCHD_PLIST\""
else
  echo "Did not write to ~/Library/LaunchAgents."
  echo "To copy it there explicitly:"
  echo "  LOCALAI_WRITE_LAUNCHD=true bash scripts/create_launchd_plist.sh"
  echo "Then review and load manually:"
  echo "  launchctl load \"$LAUNCHD_PLIST\""
fi
