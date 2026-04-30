import re
from dataclasses import dataclass
from typing import Iterable

from app.schemas import ResearchRun


ALLOWED_EVIDENCE_LABELS = {
    "Data",
    "Source claim",
    "Framework inference",
    "Narrative signal",
    "Open question",
}

SAFE_DISCLAIMER_PATTERNS = [
    re.compile(r"\bthis is not a buy/sell recommendation\b", re.I),
    re.compile(r"\bnot a buy/sell recommendation\b", re.I),
    re.compile(r"\bno buy/sell recommendations?\b", re.I),
    re.compile(r"\bdoes not present price targets?\b", re.I),
    re.compile(r"\bno price targets?\b", re.I),
    re.compile(r"\bnot investment advice\b", re.I),
]

FORBIDDEN_PATTERNS = [
    re.compile(r"\bstrong\s+(buy|sell)\b", re.I),
    re.compile(
        r"\b(we|you|investors?)\s+should\s+"
        r"(buy|sell|hold|short|accumulate)\b",
        re.I,
    ),
    re.compile(r"\brecommend(?:ed|s)?\s+(buying|selling|shorting)\b", re.I),
    re.compile(r"\b(buy|sell|hold)\s+(the\s+)?(stock|shares|equity)\b", re.I),
    re.compile(r"\brate[sd]?\s+.*\b(a\s+)?(buy|sell|hold)\b", re.I),
    re.compile(r"\b(price target|target price)\b", re.I),
    re.compile(r"\$\s*\d+(?:\.\d+)?\s*(price\s*)?target\b", re.I),
    re.compile(
        r"\bbased on your (portfolio|risk tolerance|financial situation|goals)\b",
        re.I,
    ),
]

FABRICATED_SOURCE_LABELS = {
    "",
    "source",
    "sources",
    "web",
    "web search",
    "internet",
    "n/a",
    "na",
    "unknown",
    "model output",
    "ai generated",
    "future macro + bank kpi pack",
    "data placeholder",
}


@dataclass(frozen=True)
class SafetyResult:
    passed: bool
    reasons: tuple[str, ...] = ()


def validate_agentic_research_run(
    run: ResearchRun,
    *,
    verified_source_labels: Iterable[str] | None = None,
) -> SafetyResult:
    reasons: list[str] = []
    verified_source_label_set = (
        {
            _normalize_source_label(source_label)
            for source_label in verified_source_labels
            if source_label.strip()
        }
        if verified_source_labels is not None
        else None
    )

    if not run.transmissionNodes or not run.transmissionEdges:
        reasons.append("transmission map is empty")
    if not run.charts:
        reasons.append("charts are empty")
    if not run.evidence:
        reasons.append("evidence board is empty")
    if not run.memo:
        reasons.append("memo is empty")
    if not run.openQuestions:
        reasons.append("open questions are empty")

    evidence_labels = {item.type for item in run.evidence}
    node_labels = {node.evidenceType for node in run.transmissionNodes}
    if not evidence_labels <= ALLOWED_EVIDENCE_LABELS:
        reasons.append("evidence label drift")
    if not node_labels <= ALLOWED_EVIDENCE_LABELS:
        reasons.append("node evidence label drift")

    text_blob = _safe_text_blob(_iter_run_text(run))
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text_blob):
            reasons.append("forbidden recommendation or price-target language")
            break

    for item in run.evidence:
        if item.type != "Data":
            continue
        source_label = (item.sourceLabel or "").strip()
        normalized_source_label = _normalize_source_label(source_label)
        if verified_source_label_set is None:
            reasons.append("Data evidence requires verified source research")
            break
        if normalized_source_label in FABRICATED_SOURCE_LABELS:
            reasons.append("Data evidence has weak source label")
            break
        if normalized_source_label not in verified_source_label_set:
            reasons.append("Data evidence source label is not verified")
            break

    return SafetyResult(
        passed=not reasons,
        reasons=tuple(reasons),
    )


def _safe_text_blob(chunks: Iterable[str]) -> str:
    text = "\n".join(chunk for chunk in chunks if chunk)
    for pattern in SAFE_DISCLAIMER_PATTERNS:
        text = pattern.sub("", text)
    return text


def _normalize_source_label(source_label: str) -> str:
    return " ".join(source_label.strip().lower().split())


def _iter_run_text(run: ResearchRun) -> Iterable[str]:
    yield run.question
    yield run.classification
    yield run.scenario
    yield run.headline
    yield run.thesis
    yield run.judgment.title
    yield run.judgment.stance
    yield run.judgment.summary
    yield from run.judgment.watchItems
    yield from run.keyDrivers

    for metric in run.metrics:
        yield metric.label
        yield metric.value
        yield metric.detail

    for agent in run.agents:
        yield agent.name
        yield agent.role
        yield from agent.output

    for node in run.transmissionNodes:
        yield node.label
        yield node.subtitle
        yield node.driver
        yield node.researchImplication
        yield node.whyItMatters

    for edge in run.transmissionEdges:
        yield edge.label

    for chart in run.charts:
        yield chart.title
        yield chart.subtitle
        yield chart.unit

    for item in run.evidence:
        yield item.claim
        yield item.driver
        yield item.sourceLabel or ""
        yield item.sourceType or ""
        yield item.sourceQuality or ""

    yield run.bullCase.title
    yield from run.bullCase.points
    yield run.bearCase.title
    yield from run.bearCase.points

    for section in run.memo:
        yield section.title
        yield section.body

    for question in run.openQuestions:
        yield question.question
        yield question.whyItMatters
        yield question.owner
