#!/usr/bin/env python3
"""Safe local diagnostics for the ResearchOS OpenAI adapter.

This script intentionally prints only fixed-prompt and metadata-level
diagnostics. It does not print API keys, raw full prompts, raw responses, or
tracebacks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.agentic.config import get_agentic_research_config
from app.agentic.models import PlannerStageResult
from app.agentic.openai_client import AgenticResearchError, OpenAIResearchClient
from app.agentic.prompts import PLANNER_PROMPT


SAFE_TEST_PROMPT = "How would a stronger US dollar affect semiconductor earnings?"


class _CapturingResponsesEndpoint:
    def __init__(self, wrapped: Any) -> None:
        self._wrapped = wrapped
        self.last_response: Any | None = None

    def create(self, **kwargs: Any) -> Any:
        self.last_response = self._wrapped.create(**kwargs)
        return self.last_response


class _CapturingSDKClient:
    def __init__(self, wrapped: Any) -> None:
        self.responses = _CapturingResponsesEndpoint(wrapped.responses)


def main() -> int:
    config = get_agentic_research_config()
    _print_config(config)

    if not config.api_key:
        _print("basic_sdk_success", "false")
        _print("planner_structured_success", "false")
        _print("diagnostic_error", "OPENAI_API_KEY is not configured")
        return 2

    basic_ok = _run_basic_sdk_check(config)
    planner_ok = _run_planner_adapter_check(config)
    return 0 if basic_ok and planner_ok else 1


def _print_config(config: Any) -> None:
    _print("config_model", config.model)
    _print("config_max_output_tokens", str(config.max_output_tokens))
    _print("config_reasoning_effort", config.reasoning_effort)
    _print("config_timeout_seconds", str(config.timeout_seconds))
    _print("config_web_search_enabled", str(config.web_search_enabled).lower())
    _print("api_key_present", str(bool(config.api_key)).lower())
    _print("fixed_prompt", SAFE_TEST_PROMPT)


def _run_basic_sdk_check(config: Any) -> bool:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.api_key, timeout=config.timeout_seconds)
        response = client.responses.create(
            model=config.model,
            input="Return exactly: ok",
            store=False,
            reasoning={"effort": config.reasoning_effort},
            max_output_tokens=min(config.max_output_tokens, 200),
        )
    except Exception as exc:
        _print("basic_sdk_success", "false")
        _print("basic_error_type", type(exc).__name__)
        _print("basic_error_cause_class", _cause_class_name(exc))
        _print("basic_response_status", _response_status_from_exception(exc))
        return False

    _print("basic_sdk_success", "true")
    _print("basic_response_status", _response_status(response))
    return True


def _run_planner_adapter_check(config: Any) -> bool:
    try:
        from openai import OpenAI

        sdk_client = _CapturingSDKClient(
            OpenAI(api_key=config.api_key, timeout=config.timeout_seconds)
        )
        client = OpenAIResearchClient(config, sdk_client=sdk_client)
        parsed = client.create_structured_response(
            stage_name="agentic_planner",
            instructions=PLANNER_PROMPT,
            schema=PlannerStageResult.model_json_schema(),
            input_data={"question": SAFE_TEST_PROMPT},
        )
        PlannerStageResult.model_validate(parsed)
    except AgenticResearchError as exc:
        _print("planner_structured_success", "false")
        _print("planner_error_reason", exc.reason)
        _print("planner_error_safe_detail", exc.safe_detail or "none")
        _print("planner_error_cause_class", _cause_class_name(exc))
        _print("planner_response_status", _response_status_from_exception(exc))
        return False
    except Exception as exc:
        _print("planner_structured_success", "false")
        _print("planner_error_reason", "unexpected_error")
        _print("planner_error_type", type(exc).__name__)
        _print("planner_error_cause_class", _cause_class_name(exc))
        _print("planner_response_status", _response_status_from_exception(exc))
        return False

    _print("planner_structured_success", "true")
    _print(
        "planner_response_status",
        _response_status(sdk_client.responses.last_response),
    )
    _print("planner_validated", "true")
    return True


def _response_status(value: Any) -> str:
    status = getattr(value, "status", None)
    if isinstance(status, str) and status:
        return status[:80]
    return "unavailable"


def _response_status_from_exception(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return str(status_code)

    cause = exc.__cause__
    while cause is not None:
        status_code = getattr(cause, "status_code", None)
        if isinstance(status_code, int):
            return str(status_code)
        response = getattr(cause, "response", None)
        response_status = getattr(response, "status_code", None)
        if isinstance(response_status, int):
            return str(response_status)
        cause = cause.__cause__

    return "unavailable"


def _cause_class_name(exc: Exception) -> str:
    cause = exc.__cause__
    if cause is None:
        return "none"
    return type(cause).__name__[:80]


def _print(key: str, value: str) -> None:
    print(f"{key}={value}")


if __name__ == "__main__":
    raise SystemExit(main())
