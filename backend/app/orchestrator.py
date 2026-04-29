from app.case_router import DemoCase, route_question
from app.demo_cases import (
    AI_CAPEX_SEMIS_RESEARCH_RUN,
    CANADIAN_BANKS_RESEARCH_RUN,
    OIL_AIRLINES_RESEARCH_RUN,
)
from app.schemas import ResearchRun, ResearchRunRequest


_CASE_RUNS: dict[DemoCase, ResearchRun] = {
    "canadian_banks": CANADIAN_BANKS_RESEARCH_RUN,
    "oil_airlines": OIL_AIRLINES_RESEARCH_RUN,
    "ai_capex_semis": AI_CAPEX_SEMIS_RESEARCH_RUN,
}


def run_research_pipeline(request: ResearchRunRequest) -> ResearchRun:
    selected_case = _CASE_RUNS[route_question(request.question)]
    display_question = request.question.strip() or selected_case.question

    return selected_case.model_copy(
        deep=True,
        update={"question": display_question},
    )
