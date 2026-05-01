from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import (
    BullBearCase,
    EvidenceItem,
    MemoSection,
    OpenQuestion,
    ResearchRun,
    TransmissionEdge,
    TransmissionNode,
)
from app.schemas.research_run import Confidence, Polarity


class PlannerStageResult(BaseModel):
    researchType: str
    shock: str
    affectedEntities: list[str]
    drivers: list[str]
    scope: Literal["in_scope", "out_of_scope"]
    researchObjective: str
    rejectedReason: str | None = None


class SourceNote(BaseModel):
    sourceLabel: str
    sourceType: str
    sourceQuality: Literal["High", "Medium", "Low"]
    claim: str
    relevance: str
    openQuestions: list[str] = []


class SourceResearchResult(BaseModel):
    sourceNotes: list[SourceNote]
    openQuestions: list[str] = []


class FrameworkStageResult(BaseModel):
    transmissionNodes: list[TransmissionNode]
    transmissionEdges: list[TransmissionEdge]
    evidence: list[EvidenceItem]


class SkepticStageResult(BaseModel):
    bearCase: BullBearCase
    openQuestions: list[OpenQuestion]
    evidence: list[EvidenceItem]


class SynthesisStageResult(BaseModel):
    researchRun: ResearchRun


FastEvidenceType = Literal[
    "Framework inference",
    "Narrative signal",
    "Open question",
]


class FastTransmissionPoint(BaseModel):
    label: str
    subtitle: str
    driver: str
    evidenceType: FastEvidenceType
    confidence: Confidence
    researchImplication: str
    whyItMatters: str
    polarity: Polarity


class FastEvidenceClaim(BaseModel):
    claim: str
    type: FastEvidenceType
    confidence: Confidence
    importance: Literal["Low", "Medium", "High"]
    driver: str
    sourceLabel: str
    sourceType: str
    sourceQuality: Literal["Medium", "Low"]


class FastOpenQuestion(BaseModel):
    question: str
    whyItMatters: str
    owner: str


class FastSynthesisStageResult(BaseModel):
    researchType: str
    shock: str
    affectedEntities: list[str] = Field(min_length=1, max_length=5)
    headline: str
    thesis: str
    keyDrivers: list[str] = Field(min_length=3, max_length=6)
    transmission: list[FastTransmissionPoint] = Field(
        min_length=3,
        max_length=5,
    )
    evidence: list[FastEvidenceClaim] = Field(min_length=3, max_length=6)
    bullCaseTitle: str
    bullCasePoints: list[str] = Field(min_length=2, max_length=4)
    bearCaseTitle: str
    bearCasePoints: list[str] = Field(min_length=2, max_length=4)
    memoSections: list[MemoSection] = Field(min_length=3, max_length=4)
    openQuestions: list[FastOpenQuestion] = Field(min_length=2, max_length=5)
