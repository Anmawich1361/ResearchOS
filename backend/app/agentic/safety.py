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
    re.compile(
        r"\bdo not (?:give|provide) me (?:a\s+)?"
        r"(?:price target|target price)\b",
        re.I,
    ),
    re.compile(r"\bexplain why price targets? can be unreliable\b", re.I),
    re.compile(
        r"\bwithout (?:giving|providing) (?:a\s+)?"
        r"(?:price target|target price)\b",
        re.I,
    ),
    re.compile(r"\bwithout recommendations?\b", re.I),
    re.compile(r"\bnot investment advice\b", re.I),
]

FORBIDDEN_RESEARCH_INTENT_PATTERNS = [
    re.compile(
        r"\bshould\s+(i|we|you|investors?)\s+"
        r"(buy|sell|hold|short|accumulate)\b",
        re.I,
    ),
    re.compile(
        r"\b(i|we|you|investors?)\s+should\s+"
        r"(buy|sell|hold|short|accumulate)\b",
        re.I,
    ),
    re.compile(
        r"\bwould\s+you\s+(buy|sell|hold|short|accumulate)\b",
        re.I,
    ),
    re.compile(
        r"\bdo\s+you\s+recommend\s+"
        r"(buying|selling|holding|shorting|accumulating)\b",
        re.I,
    ),
    re.compile(
        r"\brecommend(?:ed|s)?\s+"
        r"(buying|selling|holding|shorting|accumulating)\b",
        re.I,
    ),
    re.compile(
        r"\bis\s+.{1,80}?\s+(a|an)\s+"
        r"(buy|sell|hold|short|accumulate)\b",
        re.I,
    ),
    re.compile(
        r"\bwhat\s+(?:is|are)\s+(?:the\s+|a\s+)?"
        r"(?:price target|target price)\s+for\b",
        re.I,
    ),
    re.compile(
        r"\bwhat(?:\s+is|'s)\s+(?:your\s+)?"
        r"(?:price target|target price)\s+(?:on|for|of)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:price target|target price)\s+(?:on|for|of)\b",
        re.I,
    ),
    re.compile(
        r"\bgive\s+me\s+(?:a\s+|the\s+)?"
        r"(?:price target|target price)\b",
        re.I,
    ),
    re.compile(
        r"\bwhat(?:\s+is|'s)\s+(?:your\s+)?pt\s+(?:on|for|of)\b",
        re.I,
    ),
    re.compile(r"\bgive\s+me\s+(?:a\s+)?pt\s+(?:on|for|of)\b", re.I),
    re.compile(
        r"\bwhat\s+should\s+my\s+"
        r"(?:price target|target price)\s+be\b",
        re.I,
    ),
    re.compile(
        r"\bwhat\s+is\s+fair\s+"
        r"(?:upside|downside|upside\s*/\s*downside|upside/downside)\s+"
        r"to\s+my\s+(?:price target|target price)\b",
        re.I,
    ),
    re.compile(
        r"\bhow\s+much\s+of\s+my\s+portfolio\s+should\s+i\s+"
        r"(?:put|allocate|invest)\b",
        re.I,
    ),
    re.compile(
        r"\bwhat\s+portfolio\s+allocation\s+should\s+i\s+use\b",
        re.I,
    ),
    re.compile(
        r"\bwhat\s+allocation\s+should\s+i\s+use\b.*\bmy\s+portfolio\b",
        re.I,
    ),
    re.compile(
        r"\bwhat\s+(?:percent|percentage|%)\s+of\s+my\s+portfolio\s+"
        r"should\s+(?:be|i\s+(?:put|allocate|invest))\b",
        re.I,
    ),
    re.compile(
        r"\bshould\s+i\s+allocate\s+"
        r"(?:\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s+percent)\s+"
        r"of\s+my\s+portfolio\b",
        re.I,
    ),
    re.compile(
        r"\b(?:tfsa|rrsp|ira|401k|401\(k\)|investment account)\b.*"
        r"\b(?:allocate|allocation|position|overweight|underweight)\b",
        re.I,
    ),
    re.compile(
        r"\bhow\s+(?:large|big)\s+should\s+my\s+position\s+be\b",
        re.I,
    ),
    re.compile(
        r"\bshould\s+i\s+(?:overweight|underweight)\b.*"
        r"\bmy\s+portfolio\b",
        re.I,
    ),
    re.compile(
        r"\bbased\s+on\s+(?:my|our|your)\s+"
        r"(?:portfolio|risk tolerance|financial situation|goals)\b",
        re.I,
    ),
]

FORBIDDEN_PATTERNS = [
    re.compile(r"\bstrong\s+(buy|sell)\b", re.I),
    re.compile(r"\b(buy|sell|hold)\s+(the\s+)?(stock|shares|equity)\b", re.I),
    re.compile(r"\brate[sd]?\s+.*\b(a\s+)?(buy|sell|hold)\b", re.I),
    re.compile(
        r"\b(?:includes?|provides?|assigns?|sets?|uses?|gives?)\s+"
        r"(?:a\s+|the\s+)?(?:price target|target price)\b",
        re.I,
    ),
    re.compile(r"\b(?:price target|target price)\s+(?:is|of|at|=)\b", re.I),
    re.compile(r"\$\s*\d+(?:\.\d+)?\s*(price\s*)?target\b", re.I),
    re.compile(
        r"\bportfolio allocation\s+should\b"
        r"|\bposition\s+(?:size|sizing|should\s+be)\b"
        r"|\b(?:overweight|underweight)\b.*\bportfolio\b",
        re.I,
    ),
    re.compile(
        r"\bbased on (?:my|our|your) "
        r"(?:portfolio|risk tolerance|financial situation|goals)\b",
        re.I,
    ),
]


@dataclass(frozen=True)
class SafetyResult:
    passed: bool
    reasons: tuple[str, ...] = ()


def contains_forbidden_research_intent(text: str) -> bool:
    safe_text = _safe_text_blob([text])
    return any(
        pattern.search(safe_text)
        for pattern in FORBIDDEN_RESEARCH_INTENT_PATTERNS
    )


def contains_forbidden_advisory_intent(text: str) -> bool:
    return contains_forbidden_research_intent(text)


def validate_agentic_research_run(run: ResearchRun) -> SafetyResult:
    reasons: list[str] = []

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
    if "Data" in evidence_labels or "Data" in node_labels:
        reasons.append("agentic output cannot use Data evidence")

    text_blob = _safe_text_blob(_iter_run_text(run))
    if contains_forbidden_research_intent(text_blob):
        reasons.append("forbidden recommendation or price-target language")
    else:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text_blob):
                reasons.append(
                    "forbidden recommendation or price-target language"
                )
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
