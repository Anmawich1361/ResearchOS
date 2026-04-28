from pydantic import BaseModel

from app.agents.data_agent import DataAgentOutput
from app.agents.framework_agent import FrameworkAgentOutput
from app.agents.planner import PlannerOutput
from app.schemas import AgentStage, BullBearCase, EvidenceItem, OpenQuestion


class SkepticAgentOutput(BaseModel):
    bearCase: BullBearCase
    openQuestions: list[OpenQuestion]
    evidence: list[EvidenceItem]
    stage: AgentStage


def run_skeptic_agent(
    _: PlannerOutput, __: DataAgentOutput, ___: FrameworkAgentOutput
) -> SkepticAgentOutput:
    return SkepticAgentOutput.model_validate(
        {
            "bearCase": {
                "title": "Adverse transmission",
                "points": [
                    "Initial rate cuts may be a signal that growth and labor conditions are deteriorating.",
                    "Asset-yield repricing pressures NII before deposit-cost benefits fully appear.",
                    "Mortgage renewals and housing exposure keep the credit-loss path highly sensitive.",
                    "Higher provisions compress ROE and can offset any lower-rate multiple support.",
                ],
            },
            "openQuestions": [
                {
                    "question": "Are cuts driven by disinflation normalization or by a deteriorating labor market?",
                    "whyItMatters": "This determines whether credit relief or provision risk dominates.",
                    "owner": "Macro data follow-up",
                },
                {
                    "question": "How quickly do Canadian bank assets and deposits reprice under this scenario?",
                    "whyItMatters": "Deposit beta, asset sensitivity, and mortgage renewal timing shape the NII path.",
                    "owner": "Bank model follow-up",
                },
                {
                    "question": "Which loan books are most exposed to household refinancing stress?",
                    "whyItMatters": "Housing exposure and consumer-credit sensitivity can change the provision and ROE balance.",
                    "owner": "Sector diligence",
                },
            ],
            "evidence": [
                {
                    "claim": "The central unresolved issue is whether cuts reflect normalization or recession risk.",
                    "type": "Open question",
                    "confidence": "Medium",
                    "importance": "High",
                    "driver": "Macro regime",
                    "sourceLabel": "Skeptic agent issue list",
                    "sourceType": "Open research item",
                    "sourceQuality": "Medium",
                },
            ],
            "stage": {
                "name": "Skeptic Agent",
                "role": "Challenges the clean bullish interpretation.",
                "status": "complete",
                "duration": "00:05",
                "output": [
                    "Cuts can signal weakening growth",
                    "Housing exposure and unemployment can dominate the rate effect",
                    "Deposit beta assumptions are uncertain",
                ],
            },
        }
    )
