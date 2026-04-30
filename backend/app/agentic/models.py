from typing import Literal

from pydantic import BaseModel

from app.schemas import (
    BullBearCase,
    EvidenceItem,
    OpenQuestion,
    ResearchRun,
    TransmissionEdge,
    TransmissionNode,
)


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
