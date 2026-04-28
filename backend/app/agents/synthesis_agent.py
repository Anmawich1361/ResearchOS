from pydantic import BaseModel

from app.agents.data_agent import DataAgentOutput
from app.agents.framework_agent import FrameworkAgentOutput
from app.agents.planner import PlannerOutput
from app.agents.skeptic_agent import SkepticAgentOutput
from app.schemas import (
    AgentStage,
    BullBearCase,
    EvidenceItem,
    MemoSection,
    ResearchJudgment,
)


class SynthesisAgentOutput(BaseModel):
    headline: str
    thesis: str
    judgment: ResearchJudgment
    bullCase: BullBearCase
    memo: list[MemoSection]
    evidence: list[EvidenceItem]
    stage: AgentStage


def run_synthesis_agent(
    _: PlannerOutput,
    __: DataAgentOutput,
    ___: FrameworkAgentOutput,
    ____: SkepticAgentOutput,
) -> SynthesisAgentOutput:
    return SynthesisAgentOutput.model_validate(
        {
            "headline": "Rate cuts improve credit relief, but bank earnings depend on deposit beta, mortgage renewal timing, and asset sensitivity.",
            "thesis": "The Canadian-bank rate-cut setup is analytically mixed. Lower rates can ease household debt-service stress and eventually support loan growth, but near-term net interest income depends on how quickly assets reprice versus deposits, while housing exposure and unemployment determine whether provisions actually normalize.",
            "judgment": {
                "title": "Research judgment",
                "stance": "Balanced, credit-sensitive, not mechanically bullish",
                "summary": "Treat rate cuts as a transmission question rather than a one-factor catalyst. The constructive case requires contained unemployment, orderly mortgage renewals, falling credit losses, and enough deposit beta to protect NII. The adverse case is a recessionary easing cycle where provisions and ROE compression overwhelm multiple support.",
                "watchItems": [
                    "Deposit beta and funding-cost lag",
                    "Mortgage renewal shock absorption",
                    "Provision build versus credit-loss peaking",
                    "ROE path and valuation multiple discipline",
                ],
            },
            "bullCase": {
                "title": "Constructive transmission",
                "points": [
                    "Deposit beta protects funding costs enough to limit NII compression.",
                    "Lower renewal rates relieve household cash-flow pressure and slow credit-loss migration.",
                    "Provision builds peak earlier if unemployment and housing collateral remain orderly.",
                    "ROE durability plus lower discount rates can support valuation multiples without implying a recommendation.",
                ],
            },
            "memo": [
                {
                    "title": "Bottom line",
                    "body": "Rate cuts are not mechanically bullish for Canadian banks. The demo view is balanced: easing can reduce mortgage-renewal stress and eventually support credit outcomes, but first-order earnings pressure may appear through asset-yield repricing, NII sensitivity, and still-elevated provisions.",
                },
                {
                    "title": "Most important driver",
                    "body": "The decisive branch is whether cuts are benign normalization or recessionary easing. If employment, housing, and delinquencies hold, credit-loss and valuation branches improve. If cuts arrive because growth is rolling over, provisions and ROE pressure can dominate deposit-beta and discount-rate benefits.",
                },
                {
                    "title": "Evidence standard",
                    "body": "This prototype labels claims as data, framework inference, narrative signal, or open question and now includes source-readiness fields. It does not present price targets, buy/sell calls, live data, or unsupported company-specific conclusions.",
                },
            ],
            "evidence": [
                {
                    "claim": "Investors may reward lower discount rates only if NII and provision revisions remain contained.",
                    "type": "Narrative signal",
                    "confidence": "Low/Medium",
                    "importance": "Medium",
                    "driver": "ROE / valuation multiple",
                    "sourceLabel": "Market narrative placeholder",
                    "sourceType": "Narrative signal",
                    "sourceQuality": "Low",
                },
            ],
            "stage": {
                "name": "Synthesis Agent",
                "role": "Produces the map, evidence board, bull/bear view, and memo.",
                "status": "complete",
                "duration": "00:08",
                "output": [
                    "Transmission map assembled",
                    "Claims labeled by evidence type",
                    "Memo avoids recommendations and price targets",
                ],
            },
        }
    )
