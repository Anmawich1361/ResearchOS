# Deployment

ResearchOS is deployed as two services:

- FastAPI backend on Render
- Next.js frontend on Vercel

The backend analysis remains deterministic. The Canadian banks demo may replace
the policy-rate chart with official Bank of Canada Valet API data when
available, and otherwise falls back to deterministic demo data. Deployment
should not add OpenAI, FRED, SEC, database, auth, or live market-data
integrations.

The Bank of Canada Valet API does not require an API key.
Use `/research/data-status` to verify whether the latest Canadian banks policy
rate chart came from the live Bank of Canada feed, a fresh cache entry, or the
deterministic fallback path.

## Backend: Render

Create a new Render web service connected to this repository.

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set this environment variable:

```text
ALLOWED_ORIGINS=<vercel frontend URL>
```

Use the frontend origin only, without a path. Example:

```text
ALLOWED_ORIGINS=https://researchos.example.vercel.app
```

Use a comma-separated list if more than one fixed frontend origin should be
allowed.

Local development origins are always allowed by default:

```text
http://localhost:3000
http://127.0.0.1:3000
http://localhost:3001
http://127.0.0.1:3001
```

For Vercel preview deployments, optionally set:

```text
ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app
```

Leave `ALLOWED_ORIGIN_REGEX` unset unless preview deployments need to call the
Render backend.

## Frontend: Vercel

Create a new Vercel project connected to this repository.

- Root directory: `frontend`
- Build command: `npm run build`

Set this environment variable:

```text
NEXT_PUBLIC_API_BASE_URL=<render backend URL>
```

Use the backend base URL only, without a trailing slash or path. Example:

```text
NEXT_PUBLIC_API_BASE_URL=https://researchos-api.onrender.com
```

The frontend will call:

```text
<NEXT_PUBLIC_API_BASE_URL>/research/run
```

## Smoke Checks

After deployment:

```bash
curl https://<render-backend-host>/health
```

Expected response:

```json
{"status":"ok"}
```

Check live-data status:

```bash
curl https://<render-backend-host>/research/data-status
```

Then open the Vercel frontend and run one of the golden-path demo questions.

For the full deployed API verification flow, run:

```bash
./scripts/verify_research_api.sh https://<render-backend-host>
```

The canonical Bank of Canada marker checklist is in
`docs/boc-verification.md`.
