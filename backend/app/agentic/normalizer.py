from pydantic import ValidationError

from app.agentic.models import FastSynthesisStageResult, SynthesisStageResult
from app.schemas import (
    AgentStage,
    BullBearCase,
    ChartPoint,
    ChartSeries,
    EvidenceItem,
    MemoSection,
    Metric,
    OpenQuestion,
    ResearchJudgment,
    ResearchRun,
    TransmissionEdge,
    TransmissionNode,
)


class AgenticNormalizationError(ValueError):
    pass


def normalize_agentic_research_run(
    payload: dict[str, object],
    *,
    requested_question: str,
) -> ResearchRun:
    try:
        synthesis = SynthesisStageResult.model_validate(payload)
    except ValidationError as exc:
        raise AgenticNormalizationError(
            "Agentic synthesis payload did not match ResearchRun schema"
        ) from exc

    run = synthesis.researchRun
    question = requested_question.strip()
    if question:
        run = run.model_copy(update={"question": question})

    return run


def normalize_fast_synthesis_research_run(
    payload: dict[str, object],
    *,
    requested_question: str,
) -> ResearchRun:
    try:
        synthesis = FastSynthesisStageResult.model_validate(payload)
    except ValidationError as exc:
        raise AgenticNormalizationError(
            "Agentic fast synthesis payload did not match schema"
        ) from exc

    question = requested_question.strip()
    nodes = _fast_transmission_nodes(synthesis)
    return ResearchRun(
        question=question,
        classification=synthesis.researchType,
        timestamp="Agentic beta run | fast synthesis",
        scenario="Agentic beta fast macro transmission",
        headline=synthesis.headline,
        thesis=synthesis.thesis,
        judgment=ResearchJudgment(
            title="Conditional macro-transmission view",
            stance="Research scenario, not investment advice",
            summary=synthesis.thesis,
            watchItems=synthesis.openQuestions[:3],
        ),
        keyDrivers=synthesis.keyDrivers,
        metrics=[
            Metric(
                label="Shock",
                value=synthesis.shock,
                detail="Primary macro driver identified by the fast beta path.",
                tone="cyan",
            ),
            Metric(
                label="Universe",
                value=", ".join(synthesis.affectedEntities[:3]),
                detail="Affected entities are analytical scope, not recommendations.",
                tone="emerald",
            ),
            Metric(
                label="Evidence mode",
                value="Framework-only",
                detail="No live web search or independently verified Data evidence.",
                tone="amber",
            ),
        ],
        agents=_fast_agent_stages(synthesis),
        transmissionNodes=nodes,
        transmissionEdges=_fast_transmission_edges(nodes),
        charts=_fast_framework_charts(),
        evidence=_fast_evidence_items(),
        bullCase=_fast_bull_case(),
        bearCase=_fast_bear_case(),
        memo=_fast_memo_sections(synthesis),
        openQuestions=[
            OpenQuestion(
                question=item,
                whyItMatters=(
                    "It helps separate currency translation from demand, "
                    "margin, or cycle effects."
                ),
                owner="Agentic beta follow-up",
            )
            for item in synthesis.openQuestions[:4]
        ],
    )


def _fast_transmission_nodes(
    synthesis: FastSynthesisStageResult,
) -> list[TransmissionNode]:
    template = [
        {
            "label": "Dollar shock",
            "subtitle": "USD strengthens versus customer currencies",
            "driver": "FX translation",
            "evidenceType": "Framework inference",
            "confidence": "Medium",
            "researchImplication": (
                "Separate reported revenue translation from constant-currency "
                "demand."
            ),
            "whyItMatters": (
                "Semiconductor revenue is global, so exchange rates can move "
                "reported growth without changing units."
            ),
            "polarity": "negative",
            "x": 80,
            "y": 120,
        },
        {
            "label": "Demand channel",
            "subtitle": "Non-US buyers face local-currency pressure",
            "driver": "Export demand",
            "evidenceType": "Framework inference",
            "confidence": "Medium",
            "researchImplication": (
                "Check whether customer budgets, order timing, or mix change "
                "when the dollar moves."
            ),
            "whyItMatters": (
                "Currency pressure can look like softer end demand if "
                "local-currency budgets tighten."
            ),
            "polarity": "risk",
            "x": 310,
            "y": 120,
        },
        {
            "label": "Margin channel",
            "subtitle": "Pricing power and mix determine offsets",
            "driver": "Gross margin",
            "evidenceType": "Framework inference",
            "confidence": "Medium",
            "researchImplication": (
                "Compare product mix, cost base, and pricing power before "
                "drawing company-specific conclusions."
            ),
            "whyItMatters": (
                "Differentiated chips may absorb FX pressure differently from "
                "more commoditized exposure."
            ),
            "polarity": "mixed",
            "x": 540,
            "y": 120,
        },
        {
            "label": "Earnings quality",
            "subtitle": "Inventory and guidance risk shape interpretation",
            "driver": "Order timing",
            "evidenceType": "Open question",
            "confidence": "Medium",
            "researchImplication": (
                "Test whether FX effects coincide with inventory digestion or "
                "customer pushouts."
            ),
            "whyItMatters": (
                "The same currency shock is more consequential if it arrives "
                "during a cyclical order slowdown."
            ),
            "polarity": "risk",
            "x": 770,
            "y": 120,
        },
    ]
    nodes: list[TransmissionNode] = []
    for index, point in enumerate(template):
        nodes.append(
            TransmissionNode(
                id=f"fast-{index + 1}",
                label=point["label"],
                subtitle=point["subtitle"],
                driver=point["driver"],
                evidenceType=point["evidenceType"],
                confidence=point["confidence"],
                researchImplication=point["researchImplication"],
                whyItMatters=point["whyItMatters"],
                polarity=point["polarity"],
                x=point["x"],
                y=point["y"],
            )
        )
    return nodes


def _fast_transmission_edges(
    nodes: list[TransmissionNode],
) -> list[TransmissionEdge]:
    edges: list[TransmissionEdge] = []
    for index, (source, target) in enumerate(zip(nodes, nodes[1:])):
        edges.append(
            TransmissionEdge(
                id=f"fast-edge-{index + 1}",
                source=source.id,
                target=target.id,
                label="transmits to",
                polarity=target.polarity,
            )
        )
    return edges


def _fast_framework_charts() -> list[ChartSeries]:
    return [
        ChartSeries(
            title="USD earnings transmission framework",
            subtitle=(
                "Illustrative directional pressure index; not measured data."
            ),
            unit="relative index",
            tone="cyan",
            data=[
                ChartPoint(period="Baseline", value=50, comparison=50),
                ChartPoint(period="USD +5%", value=43, comparison=50),
                ChartPoint(period="USD +10%", value=36, comparison=50),
            ],
        )
    ]


def _fast_evidence_items() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            claim=(
                "A stronger dollar can pressure reported semiconductor "
                "earnings through translation before changing underlying "
                "unit demand."
            ),
            type="Framework inference",
            confidence="Medium",
            importance="High",
            driver="FX translation",
            sourceLabel="Agentic framework synthesis",
            sourceType="Framework-only model synthesis",
            sourceQuality="Low",
        ),
        EvidenceItem(
            claim=(
                "Demand risk depends on whether non-US customers absorb the "
                "currency move, defer orders, or shift mix."
            ),
            type="Framework inference",
            confidence="Medium",
            importance="High",
            driver="Export demand",
            sourceLabel="Agentic framework synthesis",
            sourceType="Framework-only model synthesis",
            sourceQuality="Low",
        ),
        EvidenceItem(
            claim=(
                "Inventory and order timing remain open questions because they "
                "can amplify or mask currency translation effects."
            ),
            type="Open question",
            confidence="Medium",
            importance="Medium",
            driver="Order timing",
            sourceLabel="Agentic framework synthesis",
            sourceType="Framework-only model synthesis",
            sourceQuality="Low",
        ),
    ]


def _fast_bull_case() -> BullBearCase:
    return BullBearCase(
        title="What could cushion the shock",
        points=[
            "High pricing power and differentiated products can reduce FX pass-through.",
            "US-dollar cost structures can offset part of reported translation pressure.",
        ],
    )


def _fast_bear_case() -> BullBearCase:
    return BullBearCase(
        title="What could amplify the shock",
        points=[
            "Local-currency customer budgets may weaken while reported revenue translates lower.",
            "Inventory digestion could make FX pressure look like broader demand weakness.",
        ],
    )


def _fast_memo_sections(
    synthesis: FastSynthesisStageResult,
) -> list[MemoSection]:
    return [
        MemoSection(
            title="Transmission view",
            body=synthesis.thesis,
        ),
        MemoSection(
            title="Evidence posture",
            body=(
                "This beta output is framework-only. It does not use Data "
                "evidence or independently verified citations."
            ),
        ),
        MemoSection(
            title="Research next steps",
            body=(
                "Separate constant-currency revenue, geographic mix, pricing "
                "power, and inventory indicators before forming "
                "company-specific conclusions."
            ),
        ),
    ]


def _fast_agent_stages(
    synthesis: FastSynthesisStageResult,
) -> list[AgentStage]:
    return [
        AgentStage(
            name="Planner Agent",
            role="Classifies the macro shock and semiconductor universe.",
            status="complete",
            duration="fast path",
            output=[
                f"Classified as {synthesis.researchType}.",
                f"Primary shock: {synthesis.shock}.",
            ],
        ),
        AgentStage(
            name="Framework Agent",
            role="Maps dollar strength into earnings channels.",
            status="complete",
            duration="fast path",
            output=[
                "Built a compact framework-only transmission map.",
                "Used no Data evidence in agentic output.",
            ],
        ),
        AgentStage(
            name="Skeptic Agent",
            role="Flags uncertainty and alternative interpretations.",
            status="complete",
            duration="fast path",
            output=[
                "Separated translation pressure from demand and mix effects.",
                "Kept open questions explicit.",
            ],
        ),
        AgentStage(
            name="Synthesis Agent",
            role="Normalizes output into the ResearchRun workbench schema.",
            status="complete",
            duration="fast path",
            output=[
                "Produced a non-advisory beta research run.",
                "Preserved the existing ResearchRun schema.",
            ],
        ),
    ]
