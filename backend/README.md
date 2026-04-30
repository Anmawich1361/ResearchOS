# ResearchOS Backend

FastAPI backend for the Financial Research OS macro transmission demo and
optional Agentic beta.

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Demo endpoint

```bash
curl -X POST http://127.0.0.1:8000/research/run \
  -H "Content-Type: application/json" \
  -d '{"question":"How would rate cuts affect Canadian banks?"}'
```

Milestone 2 intentionally returns deterministic demo data for the Canadian
banks/rate-cuts, oil/airlines, and AI capex/semis-cloud golden paths. The
Canadian banks demo may replace the policy-rate chart with official Bank of
Canada Valet API data when available, and otherwise falls back to deterministic
demo data. `/research/run` remains deterministic and stable.

## Agentic beta endpoints

```bash
curl http://127.0.0.1:8000/research/agentic-status
```

```bash
curl -X POST http://127.0.0.1:8000/research/agentic-run \
  -H "Content-Type: application/json" \
  -d '{"question":"How would tariff shocks affect US industrial margins?"}'
```

`/research/agentic-run` returns the same `ResearchRun` schema as
`/research/run`. If agentic mode is disabled, missing `OPENAI_API_KEY`, fails,
or returns unsafe output, the endpoint returns deterministic fallback data.

Optional environment variables:

```text
AGENTIC_RESEARCH_ENABLED=true
OPENAI_API_KEY=<server-side key>
OPENAI_RESEARCH_MODEL=gpt-5.4-mini
AGENTIC_WEB_SEARCH_ENABLED=false
AGENTIC_RESEARCH_TIMEOUT_SECONDS=30
AGENTIC_MAX_OUTPUT_TOKENS=8000
```

The backend uses the official OpenAI Python SDK for the configured Agentic beta
request path. Tests mock the adapter and do not require live OpenAI or web
access. Do not use the beta for buy/sell recommendations, price targets,
personalized investment advice, live market-data terminal behavior, or API-key
exposure.

Use `../docs/boc-verification.md` for deployment checks. It documents the exact
`Bank of Canada Valet API` marker and the deterministic fallback behavior.
Use `../docs/agentic-research.md` for Agentic beta setup and checks.
