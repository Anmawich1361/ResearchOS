from pydantic import BaseModel

from app.schemas import AgentStage


DEFAULT_RESEARCH_QUESTION = "How would rate cuts affect Canadian banks?"


class PlannerOutput(BaseModel):
    question: str
    classification: str
    timestamp: str
    scenario: str
    shock: str
    sector: str
    keyDrivers: list[str]
    stage: AgentStage


def run_planner(question: str) -> PlannerOutput:
    research_question = question.strip() or DEFAULT_RESEARCH_QUESTION

    return PlannerOutput.model_validate(
        {
            "question": research_question,
            "classification": "macro_to_sector_shock",
            "timestamp": "Prototype run | deterministic backend pipeline",
            "scenario": "Bank of Canada easing cycle",
            "shock": "rate cuts",
            "sector": "Canadian banks",
            "keyDrivers": [
                "Deposit beta",
                "Mortgage renewals",
                "Asset sensitivity",
                "Net interest income",
                "Provisions",
                "Credit losses",
                "Housing exposure",
                "ROE / valuation multiple",
            ],
            "stage": {
                "name": "Planner Agent",
                "role": "Classifies the question and extracts the sector driver map.",
                "status": "complete",
                "duration": "00:06",
                "output": [
                    "Research type: macro_to_sector_shock",
                    "Shock: rate cuts",
                    "Affected sector: Canadian banks",
                    "Drivers: deposit beta, mortgage renewals, asset sensitivity, provisions, ROE / valuation",
                ],
            },
        }
    )
