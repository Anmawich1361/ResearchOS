import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_RESEARCH_MODEL = "gpt-5.4-mini"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_PIPELINE_TIMEOUT_SECONDS = 45
DEFAULT_MAX_OUTPUT_TOKENS = 8000
DEFAULT_REASONING_EFFORT = "minimal"
REASONING_EFFORTS = {"minimal", "low", "medium", "high"}
TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AgenticResearchConfig:
    enabled: bool
    api_key: str | None
    model: str
    web_search_enabled: bool
    timeout_seconds: float
    pipeline_timeout_seconds: float
    max_output_tokens: int
    reasoning_effort: str

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def available(self) -> bool:
        return self.enabled and self.configured

    @property
    def mode(self) -> str:
        if not self.enabled:
            return "disabled"
        if not self.configured:
            return "fallback"
        return "configured"


def get_agentic_research_config(
    env: Mapping[str, str] | None = None,
) -> AgenticResearchConfig:
    source = env if env is not None else os.environ
    timeout_seconds = _parse_timeout(
        source.get("AGENTIC_RESEARCH_TIMEOUT_SECONDS"),
        default_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    pipeline_timeout_seconds = _parse_timeout(
        source.get("AGENTIC_PIPELINE_TIMEOUT_SECONDS"),
        default_seconds=DEFAULT_PIPELINE_TIMEOUT_SECONDS,
    )
    max_output_tokens = _parse_max_output_tokens(
        source.get("AGENTIC_MAX_OUTPUT_TOKENS")
    )

    return AgenticResearchConfig(
        enabled=_is_truthy(source.get("AGENTIC_RESEARCH_ENABLED")),
        api_key=(source.get("OPENAI_API_KEY") or "").strip() or None,
        model=(
            source.get("OPENAI_RESEARCH_MODEL") or DEFAULT_RESEARCH_MODEL
        ).strip(),
        web_search_enabled=_is_truthy(
            source.get("AGENTIC_WEB_SEARCH_ENABLED")
        ),
        timeout_seconds=timeout_seconds,
        pipeline_timeout_seconds=pipeline_timeout_seconds,
        max_output_tokens=max_output_tokens,
        reasoning_effort=_parse_reasoning_effort(
            source.get("AGENTIC_REASONING_EFFORT")
        ),
    )


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY_VALUES


def _parse_timeout(
    value: str | None,
    *,
    default_seconds: float,
) -> float:
    if not value:
        return float(default_seconds)

    try:
        parsed = float(value)
    except ValueError:
        return float(default_seconds)

    if parsed <= 0:
        return float(default_seconds)

    return parsed


def _parse_max_output_tokens(value: str | None) -> int:
    if not value:
        return DEFAULT_MAX_OUTPUT_TOKENS

    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_MAX_OUTPUT_TOKENS

    if parsed <= 0:
        return DEFAULT_MAX_OUTPUT_TOKENS

    return parsed


def _parse_reasoning_effort(value: str | None) -> str:
    parsed = (value or DEFAULT_REASONING_EFFORT).strip().lower()
    if parsed not in REASONING_EFFORTS:
        return DEFAULT_REASONING_EFFORT
    return parsed
