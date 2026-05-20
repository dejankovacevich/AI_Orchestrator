#!/usr/bin/env bash
# Export the full Postgres audit trail for one work packet as a single JSON file.
#
# Usage:
#   bash scripts/export_audit.sh <packet-id> [output-file]
#
# What it dumps (joined into one JSON document):
#   - the work_packets row
#   - all clarification_questions rows (every round)
#   - all execution_runs rows for the packet
#   - all model_calls rows (one per inference attempt)
#   - all evaluations rows (one per evaluator pass)
#   - all artifacts rows (one per file the runner wrote)
#   - all memory_candidates rows produced by the packet's runs
#
# Use case: a reviewer (regulator, auditor, customer security) asks "show
# me everything this system did for that packet". This script gives them
# one self-contained JSON they can read offline.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/export_audit.sh <packet-id> [output-file]" >&2
  exit 2
fi

PACKET_ID="$1"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="${2:-audit-${PACKET_ID}-${TIMESTAMP}.json}"

if ! docker exec localai-postgres pg_isready -U localai -d localai >/dev/null 2>&1; then
  echo "Postgres container is not reachable. Run: bash scripts/start_services.sh" >&2
  exit 2
fi

# Build one JSON document by joining the eight tables related to one packet.
TMP="$(mktemp)"
docker exec -i localai-postgres psql -U localai -d localai -t -A <<SQL > "$TMP"
SELECT json_build_object(
    'export_generated_at', now(),
    'work_packet_id', '$PACKET_ID',
    'work_packet', (
        SELECT to_jsonb(w)
        FROM work_packets w
        WHERE w.id = '$PACKET_ID'
    ),
    'clarification_questions', COALESCE((
        SELECT json_agg(to_jsonb(q) ORDER BY q.round_number, q.priority DESC)
        FROM clarification_questions q
        WHERE q.work_packet_id = '$PACKET_ID'
    ), '[]'::json),
    'execution_runs', COALESCE((
        SELECT json_agg(to_jsonb(r) ORDER BY r.started_at)
        FROM execution_runs r
        WHERE r.work_packet_id = '$PACKET_ID'
    ), '[]'::json),
    'model_calls', COALESCE((
        SELECT json_agg(to_jsonb(m) ORDER BY m.created_at)
        FROM model_calls m
        WHERE m.work_packet_id = '$PACKET_ID'
    ), '[]'::json),
    'evaluations', COALESCE((
        SELECT json_agg(to_jsonb(e) ORDER BY e.created_at)
        FROM evaluations e
        WHERE e.work_packet_id = '$PACKET_ID'
    ), '[]'::json),
    'artifacts', COALESCE((
        SELECT json_agg(to_jsonb(a) ORDER BY a.created_at)
        FROM artifacts a
        WHERE a.work_packet_id = '$PACKET_ID'
    ), '[]'::json),
    'memory_candidates', COALESCE((
        SELECT json_agg(to_jsonb(mc) ORDER BY mc.created_at)
        FROM memory_candidates mc
        WHERE mc.source_artifact_id IN (
            SELECT id FROM artifacts WHERE work_packet_id = '$PACKET_ID'
        )
    ), '[]'::json)
);
SQL

# Reject empty packet exports (typo in id, packet doesn't exist, etc.)
if ! grep -q '"work_packet": *{' "$TMP"; then
  echo "No work_packet row found for id $PACKET_ID. Check the id with:" >&2
  echo "  docker exec -it localai-postgres psql -U localai -d localai \\" >&2
  echo "    -c \"SELECT id, title FROM work_packets ORDER BY created_at DESC LIMIT 10;\"" >&2
  rm -f "$TMP"
  exit 2
fi

# Pretty-print so the file is reviewer-friendly.
python3 -m json.tool < "$TMP" > "$OUTPUT"
rm -f "$TMP"
echo "Wrote $OUTPUT"
echo "Rows in this export:"
python3 - <<PY
import json, sys
with open("$OUTPUT") as fp:
    data = json.load(fp)
for key in ("clarification_questions", "execution_runs", "model_calls",
            "evaluations", "artifacts", "memory_candidates"):
    rows = data.get(key) or []
    print(f"  {key:25s} {len(rows)} row(s)")
PY
