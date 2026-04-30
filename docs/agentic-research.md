# Agentic Research Beta

ResearchOS now has two research paths:

- `POST /research/run` remains the deterministic golden-path demo endpoint.
- `POST /research/agentic-run` is an optional agentic beta endpoint that returns
  the same `ResearchRun` response schema.

The agentic beta is off by default. If it is disabled, unconfigured, returns
invalid output, or fails safety validation, ResearchOS falls back to the
deterministic demo data.

## Environment

```text
AGENTIC_RESEARCH_ENABLED=true
OPENAI_API_KEY=<server-side key>
OPENAI_RESEARCH_MODEL=gpt-5.4-mini
AGENTIC_WEB_SEARCH_ENABLED=false
AGENTIC_RESEARCH_TIMEOUT_SECONDS=30
AGENTIC_MAX_OUTPUT_TOKENS=8000
```

Only `AGENTIC_RESEARCH_ENABLED=true` and `OPENAI_API_KEY` are required to make
the beta configured. `OPENAI_RESEARCH_MODEL` defaults to `gpt-5.4-mini`.
`AGENTIC_WEB_SEARCH_ENABLED` must be explicitly enabled before the source
research stage can request web search.
`AGENTIC_MAX_OUTPUT_TOKENS` defaults to `8000` so reasoning models have room to
produce complete structured JSON.

Do not expose `OPENAI_API_KEY` to the frontend. Use `/research/agentic-status`
to inspect capability status without exposing secrets.

The configured Agentic beta request path uses the official OpenAI Python SDK
with Responses API structured output. Request failures are converted to safe
fallback reason codes, and deterministic demo data remains the correctness
fallback.

## Workflow

The backend runs explicit Python orchestration:

```text
Planner -> Source research -> Framework -> Skeptic -> Synthesis
```

The stages classify the question, gather compact source notes when configured,
build a macro-transmission map, challenge the thesis, and normalize the result
into the existing `ResearchRun` schema.

When web search is disabled, the source stage stays in framework-only mode: it
may produce compact context notes and open questions, but it must not claim live
source verification or use `Data` evidence.

The output must preserve the exact evidence labels:

- Data
- Source claim
- Framework inference
- Narrative signal
- Open question

For this MVP, accepted agentic model output cannot use `Data` evidence because
model-authored source notes are not independently verified citations. Agentic
source-backed claims should use `Source claim`, while `Data` remains available
for deterministic fixtures and official deterministic integrations such as the
Bank of Canada Valet API. Real agentic `Data` evidence requires independently
extracted and verified citations in a later milestone.

The product remains non-advisory. The beta must not produce buy/sell
recommendations, price targets, or personalized investment advice.

## Local Testing

Backend tests mock OpenAI and do not require live web access:

```bash
cd backend
source .venv/bin/activate
python3 -m unittest discover -s tests
```

To smoke-test a running backend:

```bash
./scripts/verify_agentic_research_api.sh http://127.0.0.1:8000
```

Fallback responses are acceptable when agentic mode is disabled or
unconfigured.

To compare basic OpenAI SDK connectivity with the ResearchOS planner structured
request, run the safe local adapter diagnostic from the backend virtual
environment:

```bash
cd backend
.venv/bin/python ../scripts/debug_agentic_openai_adapter.py
```

The diagnostic requires `OPENAI_API_KEY` and prints only metadata-level status,
reason, and exception-class information.

## Local live agentic verification

For a local end-to-end configured-agentic smoke test, keep server-side secrets
outside the repo:

```bash
mkdir -p ~/.researchos
cat > ~/.researchos/secrets.env <<'EOF'
OPENAI_API_KEY=<server-side key>
OPENAI_RESEARCH_MODEL=gpt-5
AGENTIC_RESEARCH_ENABLED=true
AGENTIC_WEB_SEARCH_ENABLED=false
EOF
chmod 600 ~/.researchos/secrets.env
./scripts/run_agentic_live_local.sh
```

Do not commit secrets or paste API keys into prompts. The script starts a local
backend on port `8010` by default, or `RESEARCHOS_AGENTIC_TEST_PORT` if set, and
does not print the API key. It prints only safe status and fallback diagnostics.
Fallback is acceptable when `lastFallbackStage`, `lastFallbackReason`, or
`lastErrorType` is specific enough to guide follow-up.

## Troubleshooting

If `/research/agentic-status` reports `configured=true` but
`/research/agentic-run` returns the deterministic Canadian banks fallback,
inspect backend logs for the concise agentic fallback `stage` and `reason`.
The status endpoint also exposes safe last-run fields such as
`lastFallbackReason`, `lastFallbackStage`, `lastRunAt`, `lastSucceededAt`, and
`lastErrorType`.
`scripts/debug_agentic_local.sh` prints these fields after a local smoke test so
stage-specific fallback reasons can be checked without exposing prompts,
responses, or secrets.

A direct OpenAI Responses API call succeeding only confirms basic credentials
and model access. The staged ResearchOS pipeline can still fall back if the
structured output is incomplete, cannot be parsed, fails Pydantic
normalization, uses rejected evidence labels, includes advisory language, or
otherwise fails safety validation.

Agentic `Data` evidence is intentionally rejected until independent citation
extraction and verification exist. Model-authored source notes should normalize
to `Source claim`.

Keep the Agentic beta disabled in production until the structured pipeline,
safety checks, and fallback diagnostics have been validated.
