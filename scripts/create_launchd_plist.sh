#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT_PLIST="launchd/com.localai.orchestrator.nightly.plist"
LAUNCHD_PLIST="$HOME/Library/LaunchAgents/com.localai.orchestrator.nightly.plist"
PROJECT_DIR="$PWD"

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
    <integer>1</integer>
    <key>Minute</key>
    <integer>30</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>$HOME/LocalAI/logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/LocalAI/logs/launchd.err.log</string>
</dict>
</plist>
PLIST

echo "Created project-local plist at $PROJECT_PLIST"

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
