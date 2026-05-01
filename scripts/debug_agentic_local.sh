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
STATUS_AFTER_JSON="$TMP_DIR/agentic-status-after.json"
RUN_JSON="$TMP_DIR/agentic-run.json"

printf 'Checking %s/research/agentic-status\n' "$API_BASE"
if ! curl -sS --fail --max-time 20 "$API_BASE/research/agentic-status" \
  > "$STATUS_JSON"; then
  printf 'agentic-status request failed\n' >&2
  exit 1
fi
cat "$STATUS_JSON"
printf '\n\n'

RUN_TIMEOUT_SECONDS="$(python3 - "$STATUS_JSON" <<'PY'
import json
import math
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

try:
    pipeline_timeout = float(payload.get("pipelineTimeoutSeconds"))
except (TypeError, ValueError):
    pipeline_timeout = 45.0

print(max(1, math.ceil(pipeline_timeout) + 15))
PY
)"

python3 - "$STATUS_JSON" "$RUN_TIMEOUT_SECONDS" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

print("Agentic timeout settings")
print(f"requestTimeoutSeconds={payload.get('requestTimeoutSeconds')}")
print(f"pipelineTimeoutSeconds={payload.get('pipelineTimeoutSeconds')}")
print(f"curlRunMaxTimeSeconds={sys.argv[2]}")
PY
printf '\n'

printf 'Checking %s/research/agentic-run\n' "$API_BASE"
if ! curl -sS --fail --max-time "$RUN_TIMEOUT_SECONDS" \
  -H "Content-Type: application/json" \
  --data '{"question":"How would a stronger US dollar affect semiconductor earnings?"}' \
  "$API_BASE/research/agentic-run" \
  > "$RUN_JSON"; then
  printf 'agentic-run request failed\n' >&2
  exit 1
fi
cat "$RUN_JSON"
printf '\n\n'

if ! curl -sS --fail --max-time 20 "$API_BASE/research/agentic-status" \
  > "$STATUS_AFTER_JSON"; then
  printf 'post-run agentic-status request failed\n' >&2
  exit 1
fi

python3 - "$RUN_JSON" "$STATUS_AFTER_JSON" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    run_payload = json.load(handle)
with open(sys.argv[2], "r", encoding="utf-8") as handle:
    status_payload = json.load(handle)

scenario = run_payload.get("scenario")
if scenario == "Bank of Canada easing cycle":
    print("Result appears to be deterministic fallback.")
else:
    print(f"Result scenario: {scenario}")

last_succeeded_at = status_payload.get("lastSucceededAt")
print(f"lastFallbackStage={status_payload.get('lastFallbackStage')}")
print(f"lastFallbackReason={status_payload.get('lastFallbackReason')}")
print(f"lastErrorType={status_payload.get('lastErrorType')}")
print(f"lastSucceededAtPresent={last_succeeded_at is not None}")
PY
