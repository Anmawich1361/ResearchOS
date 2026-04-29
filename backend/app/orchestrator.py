from app.case_router import DemoCase, route_question
from app.data_sources import fetch_policy_rate_chart
from app.demo_cases import (
    AI_CAPEX_SEMIS_RESEARCH_RUN,
    CANADIAN_BANKS_RESEARCH_RUN,
    OIL_AIRLINES_RESEARCH_RUN,
)
from app.schemas import ChartSeries, EvidenceItem, ResearchRun, ResearchRunRequest


_CASE_RUNS: dict[DemoCase, ResearchRun] = {
    "canadian_banks": CANADIAN_BANKS_RESEARCH_RUN,
    "oil_airlines": OIL_AIRLINES_RESEARCH_RUN,
    "ai_capex_semis": AI_CAPEX_SEMIS_RESEARCH_RUN,
}


def run_research_pipeline(request: ResearchRunRequest) -> ResearchRun:
    selected_case_name = route_question(request.question)
    selected_case = _CASE_RUNS[selected_case_name]
    display_question = request.question.strip() or selected_case.question

    run = selected_case.model_copy(
        deep=True,
        update={"question": display_question},
    )

    if selected_case_name == "canadian_banks":
        return _with_bank_of_canada_policy_rate(run)

    return run


def _with_bank_of_canada_policy_rate(run: ResearchRun) -> ResearchRun:
    try:
        live_chart = fetch_policy_rate_chart()
    except Exception:
        return run

    if live_chart is None:
        return run

    updated_charts = _replace_policy_rate_chart(run.charts, live_chart)
    if updated_charts is None:
        return run

    return run.model_copy(
        update={
            "charts": updated_charts,
            "evidence": [
                *_without_existing_boc_evidence(run.evidence),
                _bank_of_canada_evidence(),
            ],
        }
    )


def _replace_policy_rate_chart(
    charts: list[ChartSeries],
    live_chart: ChartSeries,
) -> list[ChartSeries] | None:
    updated_charts = list(charts)
    for index, chart in enumerate(updated_charts):
        if chart.title == "Policy rate path":
            updated_charts[index] = live_chart
            return updated_charts

    return None


def _without_existing_boc_evidence(
    evidence: list[EvidenceItem],
) -> list[EvidenceItem]:
    return [
        item
        for item in evidence
        if item.sourceLabel != "Bank of Canada Valet API"
    ]


def _bank_of_canada_evidence() -> EvidenceItem:
    return EvidenceItem(
        claim=(
            "The policy-rate chart uses recent Bank of Canada target "
            "overnight rate observations."
        ),
        type="Data",
        confidence="High",
        importance="High",
        driver="Policy rate",
        sourceLabel="Bank of Canada Valet API",
        sourceType="Official central bank data",
        sourceQuality="High",
    )
