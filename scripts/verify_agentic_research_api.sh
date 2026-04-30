#!/usr/bin/env bash
set -u

API_BASE="${1:-https://researchos-api.onrender.com}"
API_BASE="${API_BASE%/}"
PASS_COUNT=0
FAIL_COUNT=0
TMP_DIR="$(mktemp -d)"

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

required = (
    "question",
    "classification",
    "charts",
    "evidence",
    "transmissionNodes",
    "memo",
    "openQuestions",
)
missing = [
    key
    for key in required
    if key not in payload
    or (isinstance(payload[key], list) and not payload[key])
]
if missing:
    raise SystemExit(f"missing required fields: {', '.join(missing)}")
PY
}

json_has_no_forbidden_language() {
  python3 - "$1" <<'PY'
import json
import re
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    encoded = json.dumps(json.load(handle), sort_keys=True)

safe_patterns = [
    r"\bthis is not a buy/sell recommendation\b",
    r"\bnot a buy/sell recommendation\b",
    r"\bno buy/sell recommendations?\b",
    r"\bdoes not present price targets?\b",
    r"\bno price targets?\b",
    r"\bnot investment advice\b",
]
for pattern in safe_patterns:
    encoded = re.sub(pattern, "", encoded, flags=re.I)

for pattern in [
    r"\bstrong\s+(buy|sell)\b",
    r"\b(we|you|investors?)\s+should\s+(buy|sell|hold|short)\b",
    r"\b(price target|target price)\b",
    r"\$\s*\d+(?:\.\d+)?\s*(price\s*)?target\b",
]:
    if re.search(pattern, encoded, flags=re.I):
        raise SystemExit(f"forbidden language matched: {pattern}")
PY
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

status_json="$TMP_DIR/agentic-status.json"
if curl_json "GET" "/research/agentic-status" "$status_json"; then
  if python3 - "$status_json" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

required = {
    "enabled",
    "configured",
    "model",
    "webSearchEnabled",
    "mode",
    "notes",
}
mode = payload.get("mode")
raise SystemExit(
    0
    if required <= set(payload)
    and mode in {"disabled", "fallback", "configured"}
    and "sk-" not in json.dumps(payload).lower()
    else 1
)
PY
  then
    pass "/research/agentic-status returned safe status"
  else
    fail "/research/agentic-status shape was unexpected"
  fi
else
  fail "/research/agentic-status request failed"
fi

agentic_json="$TMP_DIR/agentic-run.json"
payload='{"question":"How would tariff shocks affect US industrial margins?"}'
if curl_json "POST" "/research/agentic-run" "$agentic_json" "$payload"; then
  if json_has_required_run_fields "$agentic_json"; then
    pass "/research/agentic-run returned ResearchRun fields"
  else
    fail "/research/agentic-run response missing ResearchRun fields"
  fi

  if json_has_no_forbidden_language "$agentic_json"; then
    pass "/research/agentic-run avoided forbidden recommendation language"
  else
    fail "/research/agentic-run contained forbidden recommendation language"
  fi
else
  fail "/research/agentic-run request failed"
fi

printf '\nSummary: %s passed, %s failed\n' "$PASS_COUNT" "$FAIL_COUNT"

if [ "$FAIL_COUNT" -ne 0 ]; then
  exit 1
fi
