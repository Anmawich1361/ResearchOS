#!/usr/bin/env bash
set -u

API_BASE="${1:-https://researchos-api.onrender.com}"
API_BASE="${API_BASE%/}"
BOC_MARKER="Bank of Canada Valet API"

PASS_COUNT=0
FAIL_COUNT=0
TMP_DIR="$(mktemp -d)"
POST_OUTPUT=""

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

pass() {
  printf 'PASS %s\n' "$1"
  PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
  printf 'FAIL %s\n' "$1" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

curl_json() {
  local method="$1"
  local path="$2"
  local output="$3"
  local payload="${4:-}"

  if [ "$method" = "POST" ]; then
    curl -sS --fail --max-time 20 --retry 2 --retry-delay 2 \
      -H "Content-Type: application/json" \
      --data "$payload" \
      "$API_BASE$path" \
      > "$output"
  else
    curl -sS --fail --max-time 20 --retry 2 --retry-delay 2 \
      "$API_BASE$path" \
      > "$output"
  fi
}

json_has_required_run_fields() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

required = ("charts", "evidence", "transmissionNodes")
missing = [
    key
    for key in required
    if not isinstance(payload.get(key), list) or not payload[key]
]
if missing:
    raise SystemExit(f"missing required fields: {', '.join(missing)}")
PY
}

json_contains_marker() {
  python3 - "$1" "$BOC_MARKER" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

marker = sys.argv[2]
encoded = json.dumps(payload, sort_keys=True)
raise SystemExit(0 if marker in encoded else 1)
PY
}

post_question() {
  local name="$1"
  local question="$2"
  local output="$TMP_DIR/$name.json"
  local payload

  payload="$(python3 - "$question" <<'PY'
import json
import sys

print(json.dumps({"question": sys.argv[1]}))
PY
)"

  if ! curl_json "POST" "/research/run" "$output" "$payload"; then
    fail "$name request failed"
    return 1
  fi

  if ! json_has_required_run_fields "$output"; then
    fail "$name response missing required run fields"
    return 1
  fi

  POST_OUTPUT="$output"
}

health_json="$TMP_DIR/health.json"
if curl_json "GET" "/health" "$health_json"; then
  if python3 - "$health_json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

raise SystemExit(0 if payload == {"status": "ok"} else 1)
PY
  then
    pass "/health returned ok"
  else
    fail "/health response was not {\"status\":\"ok\"}"
  fi
else
  fail "/health request failed"
fi

status_json="$TMP_DIR/data-status.json"
if curl_json "GET" "/research/data-status" "$status_json"; then
  if python3 - "$status_json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

status = payload.get("bankOfCanadaPolicyRate")
required = {"source", "series", "url", "cached", "lastResult"}
raise SystemExit(
    0
    if isinstance(status, dict) and required <= set(status)
    else 1
)
PY
  then
    pass "/research/data-status returned BoC status"
  else
    fail "/research/data-status shape was unexpected"
  fi
else
  fail "/research/data-status request failed"
fi

if post_question \
  "canadian-banks" \
  "How would rate cuts affect Canadian banks?"
then
  canadian_file="$POST_OUTPUT"
  if json_contains_marker "$canadian_file"; then
    pass "Canadian banks run used exact BoC marker"
  else
    pass "Canadian banks run used deterministic fallback"
  fi
fi

check_absent_marker() {
  local name="$1"
  local question="$2"
  local output

  post_question "$name" "$question" || return
  output="$POST_OUTPUT"

  if json_contains_marker "$output"; then
    fail "$name unexpectedly included exact BoC marker"
  else
    pass "$name did not include exact BoC marker"
  fi
}

check_absent_marker \
  "oil-airlines" \
  "What happens to airlines if oil prices rise while consumer demand weakens?"
check_absent_marker \
  "ai-capex" \
  "Is AI capex becoming a risk for semiconductors and hyperscalers?"
check_absent_marker \
  "unknown-fallback" \
  "Unknown custom question"
check_absent_marker \
  "mixed-oil-airlines" \
  "What happens to airlines if oil prices rise while Canadian banks face rate cuts?"
check_absent_marker \
  "mixed-ai-capex" \
  "Is AI capex becoming a risk for semiconductors while Canadian banks face BoC cuts?"

printf '\nSummary: %s passed, %s failed\n' "$PASS_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -ne 0 ]; then
  exit 1
fi
