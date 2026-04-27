from typing import Literal

from pydantic import BaseModel


EvidenceType = Literal[
    "Data",
    "Source claim",
    "Framework inference",
    "Narrative signal",
    "Open question",
]
Confidence = Literal["Low", "Low/Medium", "Medium", "Medium/High", "High"]
Polarity = Literal["positive", "negative", "mixed", "risk", "neutral"]
Tone = Literal["cyan", "emerald", "amber", "rose"]


class ResearchRunRequest(BaseModel):
    question: str


class AgentStage(BaseModel):
    name: str
    role: str
    status: Literal["complete", "active", "queued"]
    duration: str
    output: list[str]


class TransmissionNode(BaseModel):
    id: str
    label: str
    subtitle: str
    driver: str
    evidenceType: EvidenceType
    confidence: Confidence
    researchImplication: str
    whyItMatters: str
    polarity: Polarity
    x: int
    y: int


class TransmissionEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    polarity: Polarity


class ChartPoint(BaseModel):
    period: str
    value: float
    comparison: float | None = None


class ChartSeries(BaseModel):
    title: str
    subtitle: str
    unit: str
    tone: Tone
    data: list[ChartPoint]


class EvidenceItem(BaseModel):
    claim: str
    type: EvidenceType
    confidence: Confidence
    importance: Literal["Low", "Medium", "High"]
    driver: str
    sourceLabel: str | None = None
    sourceType: str | None = None
    sourceQuality: Literal["High", "Medium", "Low"] | None = None


class ResearchJudgment(BaseModel):
    title: str
    stance: str
    summary: str
    watchItems: list[str]


class BullBearCase(BaseModel):
    title: str
    points: list[str]


class MemoSection(BaseModel):
    title: str
    body: str


class OpenQuestion(BaseModel):
    question: str
    whyItMatters: str
    owner: str


class Metric(BaseModel):
    label: str
    value: str
    detail: str
    tone: Tone


class ResearchRun(BaseModel):
    question: str
    classification: str
    timestamp: str
    scenario: str
    headline: str
    thesis: str
    judgment: ResearchJudgment
    keyDrivers: list[str]
    metrics: list[Metric]
    agents: list[AgentStage]
    transmissionNodes: list[TransmissionNode]
    transmissionEdges: list[TransmissionEdge]
    charts: list[ChartSeries]
    evidence: list[EvidenceItem]
    bullCase: BullBearCase
    bearCase: BullBearCase
    memo: list[MemoSection]
    openQuestions: list[OpenQuestion]
