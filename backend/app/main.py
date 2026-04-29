import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRun, ResearchRunRequest

LOCAL_ALLOWED_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)


def _parse_allowed_origins(raw_origins: str | None) -> list[str]:
    if not raw_origins:
        return []

    return [
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


def _get_allowed_origins() -> list[str]:
    configured_origins = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
    return list(dict.fromkeys([*LOCAL_ALLOWED_ORIGINS, *configured_origins]))


app = FastAPI(title="Financial Research OS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_origin_regex=os.getenv("ALLOWED_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/research/run",
    response_model=ResearchRun,
    response_model_exclude_none=True,
)
def run_research(request: ResearchRunRequest) -> ResearchRun:
    return run_research_pipeline(request)
