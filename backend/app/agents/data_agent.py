from pydantic import BaseModel

from app.agents.planner import PlannerOutput
from app.schemas import AgentStage, ChartSeries, EvidenceItem, Metric


class DataAgentOutput(BaseModel):
    metrics: list[Metric]
    charts: list[ChartSeries]
    evidence: list[EvidenceItem]
    stage: AgentStage


def run_data_agent(_: PlannerOutput) -> DataAgentOutput:
    return DataAgentOutput.model_validate(
        {
            "metrics": [
                {
                    "label": "Policy shock",
                    "value": "-100 bps",
                    "detail": "Illustrative 12-month easing path",
                    "tone": "cyan",
                },
                {
                    "label": "Credit impulse",
                    "value": "Conditional",
                    "detail": "Depends on renewals, unemployment, and housing stress",
                    "tone": "emerald",
                },
                {
                    "label": "NII sensitivity",
                    "value": "Asset-led",
                    "detail": "Asset repricing can pressure NII before deposit beta helps",
                    "tone": "amber",
                },
                {
                    "label": "Skeptic flag",
                    "value": "Provision risk",
                    "detail": "Recessionary cuts can lift PCLs and compress ROE",
                    "tone": "rose",
                },
            ],
            "charts": [
                {
                    "title": "Policy rate path",
                    "subtitle": "Illustrative easing cycle",
                    "unit": "%",
                    "tone": "cyan",
                    "data": [
                        {"period": "Q1", "value": 5.0},
                        {"period": "Q2", "value": 4.75},
                        {"period": "Q3", "value": 4.25},
                        {"period": "Q4", "value": 4.0},
                        {"period": "Q5", "value": 3.75},
                    ],
                },
                {
                    "title": "NII sensitivity index",
                    "subtitle": "Asset repricing versus deposit beta",
                    "unit": "idx",
                    "tone": "amber",
                    "data": [
                        {"period": "Q1", "value": 100, "comparison": 100},
                        {"period": "Q2", "value": 97, "comparison": 101},
                        {"period": "Q3", "value": 95, "comparison": 100},
                        {"period": "Q4", "value": 96, "comparison": 99},
                        {"period": "Q5", "value": 98, "comparison": 99},
                    ],
                },
                {
                    "title": "Mortgage renewal stress",
                    "subtitle": "Payment-shock relief path",
                    "unit": "%",
                    "tone": "emerald",
                    "data": [
                        {"period": "Q1", "value": 7.8},
                        {"period": "Q2", "value": 7.2},
                        {"period": "Q3", "value": 6.5},
                        {"period": "Q4", "value": 5.9},
                        {"period": "Q5", "value": 5.4},
                    ],
                },
                {
                    "title": "Provision risk proxy",
                    "subtitle": "Watch PCLs and unemployment",
                    "unit": "idx",
                    "tone": "rose",
                    "data": [
                        {"period": "Q1", "value": 68},
                        {"period": "Q2", "value": 72},
                        {"period": "Q3", "value": 70},
                        {"period": "Q4", "value": 65},
                        {"period": "Q5", "value": 60},
                    ],
                },
            ],
            "evidence": [
                {
                    "claim": "Credit outcomes depend heavily on unemployment, housing exposure, and refinancing stress.",
                    "type": "Data",
                    "confidence": "High",
                    "importance": "High",
                    "driver": "Credit losses",
                    "sourceLabel": "Future macro + bank KPI pack",
                    "sourceType": "Data placeholder",
                    "sourceQuality": "High",
                },
            ],
            "stage": {
                "name": "Data Agent",
                "role": "Stages macro and banking indicators for the demo run.",
                "status": "complete",
                "duration": "00:09",
                "output": [
                    "Policy-rate path staged",
                    "Deposit beta, mortgage-renewal, and credit-loss placeholders attached",
                    "No live FRED or market-data calls in Milestone 2",
                ],
            },
        }
    )
