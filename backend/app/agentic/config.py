import os
from dataclasses import dataclass
from typing import Mapping


DEFAULT_RESEARCH_MODEL = "gpt-5.4-mini"
DEFAULT_TIMEOUT_SECONDS = 30
TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AgenticResearchConfig:
    enabled: bool
    api_key: str | None
    model: str
    web_search_enabled: bool
    timeout_seconds: float

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
        source.get("AGENTIC_RESEARCH_TIMEOUT_SECONDS")
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
    )


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUTHY_VALUES


def _parse_timeout(value: str | None) -> float:
    if not value:
        return float(DEFAULT_TIMEOUT_SECONDS)

    try:
        parsed = float(value)
    except ValueError:
        return float(DEFAULT_TIMEOUT_SECONDS)

    if parsed <= 0:
        return float(DEFAULT_TIMEOUT_SECONDS)

    return parsed
