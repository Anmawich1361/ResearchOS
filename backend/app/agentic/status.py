from app.agentic.config import (
    AgenticResearchConfig,
    get_agentic_research_config,
)
from app.agentic.diagnostics import get_agentic_diagnostics


def get_agentic_research_status(
    config: AgenticResearchConfig | None = None,
) -> dict[str, object]:
    resolved = config or get_agentic_research_config()
    notes: list[str] = []

    if not resolved.enabled:
        notes.append(
            "Agentic research is disabled; deterministic fallback is active."
        )
    elif not resolved.configured:
        notes.append(
            "OPENAI_API_KEY is not configured; deterministic fallback is active."
        )
    else:
        notes.append("Agentic research is configured.")

    if resolved.web_search_enabled:
        notes.append("Web search is enabled for the source research stage.")
    else:
        notes.append("Web search is disabled.")

    return {
        "enabled": resolved.enabled,
        "configured": resolved.configured,
        "model": resolved.model,
        "webSearchEnabled": resolved.web_search_enabled,
        "maxOutputTokens": resolved.max_output_tokens,
        "reasoningEffort": resolved.reasoning_effort,
        "mode": resolved.mode,
        "notes": notes,
        **get_agentic_diagnostics(),
    }
