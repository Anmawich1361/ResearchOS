#!/usr/bin/env bash
set -u

API_BASE="${1:-http://127.0.0.1:8000}"
API_BASE="${API_BASE%/}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

STATUS_JSON="$TMP_DIR/agentic-status.json"
RUN_JSON="$TMP_DIR/agentic-run.json"

printf 'Checking %s/research/agentic-status\n' "$API_BASE"
if ! curl -sS --fail --max-time 20 "$API_BASE/research/agentic-status" \
  > "$STATUS_JSON"; then
  printf 'agentic-status request failed\n' >&2
  exit 1
fi
cat "$STATUS_JSON"
printf '\n\n'

printf 'Checking %s/research/agentic-run\n' "$API_BASE"
if ! curl -sS --fail --max-time 60 \
  -H "Content-Type: application/json" \
  --data '{"question":"How would a stronger US dollar affect semiconductor earnings?"}' \
  "$API_BASE/research/agentic-run" \
  > "$RUN_JSON"; then
  printf 'agentic-run request failed\n' >&2
  exit 1
fi
cat "$RUN_JSON"
printf '\n\n'

python3 - "$RUN_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

scenario = payload.get("scenario")
if scenario == "Bank of Canada easing cycle":
    print("Result appears to be deterministic fallback.")
    print("Inspect backend logs for agentic fallback stage and reason.")
else:
    print(f"Result scenario: {scenario}")
PY
