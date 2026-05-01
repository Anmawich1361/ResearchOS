from pydantic import ValidationError

from app.agentic.models import FastSynthesisStageResult, SynthesisStageResult
from app.schemas import (
    AgentStage,
    BullBearCase,
    ChartPoint,
    ChartSeries,
    EvidenceItem,
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
            watchItems=[
                question.question for question in synthesis.openQuestions[:3]
            ],
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
        evidence=[
            EvidenceItem(
                claim=item.claim,
                type=item.type,
                confidence=item.confidence,
                importance=item.importance,
                driver=item.driver,
                sourceLabel=item.sourceLabel,
                sourceType=item.sourceType,
                sourceQuality=item.sourceQuality,
            )
            for item in synthesis.evidence
        ],
        bullCase=BullBearCase(
            title=synthesis.bullCaseTitle,
            points=synthesis.bullCasePoints,
        ),
        bearCase=BullBearCase(
            title=synthesis.bearCaseTitle,
            points=synthesis.bearCasePoints,
        ),
        memo=synthesis.memoSections,
        openQuestions=[
            OpenQuestion(
                question=item.question,
                whyItMatters=item.whyItMatters,
                owner=item.owner,
            )
            for item in synthesis.openQuestions
        ],
    )


def _fast_transmission_nodes(
    synthesis: FastSynthesisStageResult,
) -> list[TransmissionNode]:
    coordinates = [
        (80, 120),
        (310, 120),
        (540, 120),
        (770, 120),
        (1000, 120),
    ]
    nodes: list[TransmissionNode] = []
    for index, point in enumerate(synthesis.transmission):
        x, y = coordinates[index]
        nodes.append(
            TransmissionNode(
                id=f"fast-{index + 1}",
                label=point.label,
                subtitle=point.subtitle,
                driver=point.driver,
                evidenceType=point.evidenceType,
                confidence=point.confidence,
                researchImplication=point.researchImplication,
                whyItMatters=point.whyItMatters,
                polarity=point.polarity,
                x=x,
                y=y,
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
