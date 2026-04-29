# ResearchOS Backend

FastAPI skeleton for the Financial Research OS macro transmission demo.

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

Milestone 2 intentionally returns hardcoded demo data for the Canadian
banks/rate-cuts, oil/airlines, and AI capex/semis-cloud golden paths.
There are no OpenAI, FRED, SEC, database, auth, or live-data integrations yet.
