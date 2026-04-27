from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.demo_data import DEMO_RESEARCH_RUN
from app.schemas import ResearchRun, ResearchRunRequest

app = FastAPI(title="Financial Research OS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
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
def run_research(_: ResearchRunRequest) -> ResearchRun:
    return DEMO_RESEARCH_RUN
