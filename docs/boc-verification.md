# Bank of Canada Live-Data Verification

Use this checklist after deployment to verify whether the Canadian banks
policy-rate chart used official Bank of Canada Valet API data or deterministic
fallback data.

The exact live-data marker is:

```text
Bank of Canada Valet API
```

Do not grep only for:

```text
Bank of Canada
```

The deterministic Canadian banks fallback scenario may include that phrase, so
it is not enough to prove that the official Valet API chart was used.

The backend remains deterministic when the official Bank of Canada source is
unavailable. If the Valet API request fails, times out, or returns unexpected
data, the Canadian banks response falls back to the deterministic demo chart.

## Setup

Use the deployed backend base URL:

```bash
API_BASE="https://researchos-api.onrender.com"
```

Confirm the backend is reachable:

```bash
curl -sS "$API_BASE/health"
```

Expected response:

```json
{"status":"ok"}
```

## Data Status

The backend exposes the Bank of Canada policy-rate data-source status:

```bash
curl -sS "$API_BASE/research/data-status"
```

Look for `lastResult`:

- `live`: the latest fetch returned official Valet API data.
- `cached`: a fresh in-memory cache entry is being reused.
- `fallback`: the official source was unavailable or invalid, so the app used
  deterministic fallback behavior.
- `cooldown`: a recent official-source failure is still inside the short
  retry cooldown, so deterministic fallback remains active.
- `not_requested`: no eligible Canadian-bank policy-rate request has attempted
  the data source since the service started.

The status may also include `failureCooldownSeconds`, `inFailureCooldown`, and
`nextRetryAt` to make retry behavior easier to verify without exposing raw
payloads or tracebacks.

## Verification Script

Run the bundled script to check health, data-source status, golden-path routes,
unknown fallback, and mixed-prompt marker leakage:

```bash
./scripts/verify_research_api.sh "$API_BASE"
```

The script exits nonzero for real API failures or unexpected marker leakage. It
does not fail only because the Canadian banks question used deterministic
fallback instead of official Bank of Canada data.

## Response Checks

The canonical Canadian banks policy-rate question may show the live-data marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"How would rate cuts affect Canadian banks?"}' \
  | grep -o "Bank of Canada Valet API" || true
```

If the marker appears, the response used official source-backed data for the
policy-rate chart or related evidence. If it does not appear, the backend
returned deterministic fallback data.

Oil/airlines should not show the marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"What happens to airlines if oil prices rise while consumer demand weakens?"}' \
  | grep -o "Bank of Canada Valet API" || true
```

AI capex should not show the marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"Is AI capex becoming a risk for semiconductors and hyperscalers?"}' \
  | grep -o "Bank of Canada Valet API" || true
```

Unknown/custom fallback should not show the marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"Unknown custom question"}' \
  | grep -o "Bank of Canada Valet API" || true
```

Mixed oil/airlines prompts mentioning Canadian banks or rates should not show
the marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"What happens to airlines if oil prices rise while Canadian banks face rate cuts?"}' \
  | grep -o "Bank of Canada Valet API" || true
```

Mixed AI-capex prompts mentioning Canadian banks or rates should not show the
marker:

```bash
curl -sS "$API_BASE/research/run" \
  -H "Content-Type: application/json" \
  --data '{"question":"Is AI capex becoming a risk for semiconductors while Canadian banks face BoC cuts?"}' \
  | grep -o "Bank of Canada Valet API" || true
```

## Local Certificate Note

Local Python `urllib` may fail against the Bank of Canada endpoint because of
local certificate configuration. That is a local runtime setup issue, not proof
that the deployed backend cannot reach the source. Prefer the curl checks above
when verifying deployed behavior.
