#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
SECRETS_FILE="$HOME/.researchos/secrets.env"
DEFAULT_PORT="8010"
REQUESTED_PORT="${RESEARCHOS_AGENTIC_TEST_PORT:-$DEFAULT_PORT}"
PORT_WAS_CONFIGURED="false"

if [ -n "${RESEARCHOS_AGENTIC_TEST_PORT:-}" ]; then
  PORT_WAS_CONFIGURED="true"
fi

TMP_DIR="$(mktemp -d)"
BACKEND_PID=""
BACKEND_LOG="$TMP_DIR/backend.log"
API_BASE=""

cleanup() {
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    printf 'Stopping backend process %s\n' "$BACKEND_PID"
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

source_local_secrets() {
  if [ ! -f "$SECRETS_FILE" ]; then
    return
  fi

  local had_xtrace=0
  local source_status=0

  case "$-" in
    *x*) had_xtrace=1 ;;
  esac

  set +u
  set +x
  # shellcheck source=/dev/null
  . "$SECRETS_FILE"
  source_status=$?
  set -u
  restore_xtrace "$had_xtrace"

  if [ "$source_status" -ne 0 ]; then
    die "Failed to source ~/.researchos/secrets.env."
  fi
}

restore_xtrace() {
  if [ "$1" = "1" ]; then
    set -x
  fi
}

openai_api_key_is_missing() {
  local had_xtrace=0
  local missing=1

  case "$-" in
    *x*) had_xtrace=1 ;;
  esac

  set +x
  if [ -z "${OPENAI_API_KEY:-}" ]; then
    missing=0
  fi
  restore_xtrace "$had_xtrace"

  return "$missing"
}

export_optional_agentic_config() {
  local name

  for name in \
    AGENTIC_RESEARCH_TIMEOUT_SECONDS \
    AGENTIC_MAX_OUTPUT_TOKENS \
    AGENTIC_REASONING_EFFORT \
    AGENTIC_PIPELINE_TIMEOUT_SECONDS
  do
    if [ "${!name+x}" = "x" ]; then
      export "$name"
    fi
  done
}

select_backend_python() {
  if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
    printf '%s\n' "$BACKEND_DIR/.venv/bin/python"
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    die "backend/.venv/bin/python was not found and python3 is unavailable."
  fi

  printf 'Warning: backend/.venv/bin/python not found; using python3 from PATH.\n' >&2
  command -v python3
}

find_available_port() {
  local start_port="$1"
  local strict="$2"

  "$BACKEND_PY" - "$start_port" "$strict" <<'PY'
import socket
import sys

try:
    start_port = int(sys.argv[1])
except ValueError:
    print("Port must be an integer.", file=sys.stderr)
    raise SystemExit(2)

if start_port < 1 or start_port > 65535:
    print("Port must be between 1 and 65535.", file=sys.stderr)
    raise SystemExit(2)

strict = sys.argv[2] == "true"
stop_port = start_port if strict else min(start_port + 49, 65535)

for port in range(start_port, stop_port + 1):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        raise SystemExit(0)

raise SystemExit(1)
PY
}

wait_for_health() {
  local health_json="$TMP_DIR/health.json"
  local deadline=$((SECONDS + 60))

  while [ "$SECONDS" -lt "$deadline" ]; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      die "Backend process exited before /health returned ok. Backend output was captured but not printed."
    fi

    if curl -fsS --max-time 2 "$API_BASE/health" > "$health_json" 2>/dev/null; then
      if "$BACKEND_PY" - "$health_json" <<'PY' >/dev/null 2>&1
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

raise SystemExit(0 if payload == {"status": "ok"} else 1)
PY
      then
        printf '/health returned ok\n'
        return
      fi
    fi

    sleep 1
  done

  die "Backend /health did not return ok within 60 seconds."
}

print_safe_adapter_summary() {
  local output_file="$1"

  while IFS= read -r line; do
    case "$line" in
      config_model=*|\
      config_max_output_tokens=*|\
      config_reasoning_effort=*|\
      config_timeout_seconds=*|\
      config_web_search_enabled=*|\
      api_key_present=*|\
      basic_sdk_success=*|\
      basic_error_type=*|\
      basic_error_cause_class=*|\
      basic_response_status=*|\
      planner_structured_success=*|\
      planner_error_reason=*|\
      planner_error_safe_detail=*|\
      planner_error_cause_class=*|\
      planner_response_status=*|\
      planner_validated=*)
        printf '%s\n' "$line"
        ;;
    esac
  done < "$output_file"
}

run_openai_adapter_diagnostic() {
  local output_file="$TMP_DIR/openai-adapter.log"
  local status=0

  printf 'Running scripts/debug_agentic_openai_adapter.py\n'
  "$BACKEND_PY" "$REPO_ROOT/scripts/debug_agentic_openai_adapter.py" \
    > "$output_file" 2>&1 || status=$?

  print_safe_adapter_summary "$output_file"
  printf 'openai_adapter_exit_code=%s\n' "$status"

  if [ "$status" -ne 0 ]; then
    printf 'OpenAI adapter diagnostic did not fully pass; continuing to local API verification.\n'
  fi
}

run_local_agentic_diagnostic() {
  local output_file="$TMP_DIR/debug-agentic-local.log"
  local status=0

  printf 'Running scripts/debug_agentic_local.sh %s\n' "$API_BASE"
  AGENTIC_DEBUG_LOCAL_TIMEOUT_SECONDS="${AGENTIC_DEBUG_LOCAL_TIMEOUT_SECONDS:-180}" \
    bash "$REPO_ROOT/scripts/debug_agentic_local.sh" "$API_BASE" \
    > "$output_file" 2>&1 || status=$?

  printf 'debug_agentic_local_exit_code=%s\n' "$status"

  if [ "$status" -ne 0 ]; then
    printf 'Local agentic diagnostic returned nonzero; continuing because fallback diagnostics are useful.\n'
  fi
}

print_agentic_status_summary() {
  local status_json="$TMP_DIR/agentic-status-final.json"

  if ! curl -fsS --max-time 20 "$API_BASE/research/agentic-status" \
    > "$status_json"; then
    die "Failed to fetch /research/agentic-status."
  fi

  "$BACKEND_PY" - "$status_json" <<'PY'
import json
import sys

fields = [
    "enabled",
    "configured",
    "model",
    "webSearchEnabled",
    "lastFallbackStage",
    "lastFallbackReason",
    "lastErrorType",
    "lastSucceededAt",
]

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    payload = json.load(handle)

for field in fields:
    value = payload.get(field)
    if isinstance(value, bool):
        rendered = str(value).lower()
    elif value is None:
        rendered = "null"
    else:
        rendered = str(value)
    if len(rendered) > 240:
        rendered = rendered[:237] + "..."
    print(f"{field}={rendered}")
PY
}

source_local_secrets

if openai_api_key_is_missing; then
  printf 'OPENAI_API_KEY is not set; skipping live agentic verification.\n'
  exit 0
fi

: "${OPENAI_RESEARCH_MODEL:=gpt-5}"
: "${AGENTIC_RESEARCH_ENABLED:=true}"
: "${AGENTIC_WEB_SEARCH_ENABLED:=false}"

export OPENAI_API_KEY
export OPENAI_RESEARCH_MODEL
export AGENTIC_RESEARCH_ENABLED
export AGENTIC_WEB_SEARCH_ENABLED
export_optional_agentic_config

if ! command -v curl >/dev/null 2>&1; then
  die "curl is required but was not found."
fi

BACKEND_PY="$(select_backend_python)"

if [ ! -f "$REPO_ROOT/scripts/debug_agentic_openai_adapter.py" ]; then
  die "Missing debug script: scripts/debug_agentic_openai_adapter.py"
fi

if [ ! -f "$REPO_ROOT/scripts/debug_agentic_local.sh" ]; then
  die "Missing debug script: scripts/debug_agentic_local.sh"
fi

if ! PORT="$(find_available_port "$REQUESTED_PORT" "$PORT_WAS_CONFIGURED")"; then
  if [ "$PORT_WAS_CONFIGURED" = "true" ]; then
    die "Configured port $REQUESTED_PORT is unavailable."
  fi
  die "No available port found starting at $REQUESTED_PORT."
fi

if [ "$PORT" != "$REQUESTED_PORT" ]; then
  printf 'Port %s unavailable; using %s.\n' "$REQUESTED_PORT" "$PORT"
fi

API_BASE="http://127.0.0.1:$PORT"

printf 'Starting backend on %s\n' "$API_BASE"
(
  cd "$BACKEND_DIR" || exit 1
  exec "$BACKEND_PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
) > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

wait_for_health
run_openai_adapter_diagnostic
run_local_agentic_diagnostic
print_agentic_status_summary

printf 'Live agentic verification finished.\n'
