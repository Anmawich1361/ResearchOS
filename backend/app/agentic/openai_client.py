import json
from copy import deepcopy
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agentic.config import AgenticResearchConfig
from app.agentic.prompts import AGENTIC_SYSTEM_INSTRUCTIONS


RESPONSES_API_URL = "https://api.openai.com/v1/responses"


class AgenticResearchError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        reason: str = "openai_error",
        safe_detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.safe_detail = safe_detail


class OpenAIResearchClient:
    def __init__(self, config: AgenticResearchConfig) -> None:
        if not config.api_key:
            raise AgenticResearchError("OpenAI API key is not configured")
        self._config = config

    def create_structured_response(
        self,
        *,
        stage_name: str,
        instructions: str,
        schema: dict[str, Any],
        input_data: dict[str, Any],
        allow_web_search: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._config.model,
            "store": False,
            "max_output_tokens": self._config.max_output_tokens,
            "instructions": "\n\n".join(
                [AGENTIC_SYSTEM_INSTRUCTIONS, instructions]
            ),
            "input": json.dumps(input_data, sort_keys=True),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": stage_name,
                    "description": (
                        "Structured ResearchOS agentic research stage output."
                    ),
                    "strict": True,
                    "schema": _to_strict_json_schema(schema),
                }
            },
            "reasoning": {"effort": self._config.reasoning_effort},
        }

        if allow_web_search and self._config.web_search_enabled:
            payload["tools"] = [{"type": "web_search"}]
            payload["tool_choice"] = "required"
            payload["include"] = ["web_search_call.action.sources"]

        request = Request(
            RESPONSES_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self._config.timeout_seconds,
            ) as response:
                response_payload = json.loads(
                    response.read().decode("utf-8")
                )
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise AgenticResearchError(
                f"OpenAI Responses API request failed for {stage_name}",
                reason="request_failed",
                safe_detail=type(exc).__name__,
            ) from exc

        _raise_for_response_error(response_payload, stage_name)
        _raise_for_incomplete_response(response_payload, stage_name)

        output_text = _extract_output_text(response_payload)
        if not output_text:
            raise AgenticResearchError(
                f"OpenAI Responses API returned no text for {stage_name}",
                reason="no_output_text",
            )

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AgenticResearchError(
                f"OpenAI Responses API returned invalid JSON for {stage_name}",
                reason="invalid_json",
            ) from exc

        if not isinstance(parsed, dict):
            raise AgenticResearchError(
                f"OpenAI Responses API returned non-object JSON for {stage_name}",
                reason="non_object_json",
            )

        return parsed


def _extract_output_text(response_payload: dict[str, Any]) -> str | None:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for output_item in response_payload.get("output", []):
        if not isinstance(output_item, dict):
            continue
        if output_item.get("type") != "message":
            continue
        for content_item in output_item.get("content", []):
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                return text

    return None


def _raise_for_response_error(
    response_payload: dict[str, Any],
    stage_name: str,
) -> None:
    error = response_payload.get("error")
    if not error:
        return

    error_type = "unknown_error"
    if isinstance(error, dict):
        raw_type = error.get("type") or error.get("code")
        if isinstance(raw_type, str) and raw_type:
            error_type = raw_type[:80]
    elif isinstance(error, str):
        error_type = error[:80]

    raise AgenticResearchError(
        f"OpenAI Responses API returned an error for {stage_name}: "
        f"{error_type}",
        reason="api_error",
        safe_detail=error_type,
    )


def _raise_for_incomplete_response(
    response_payload: dict[str, Any],
    stage_name: str,
) -> None:
    if response_payload.get("status") != "incomplete":
        return

    incomplete_reason = "unknown"
    details = response_payload.get("incomplete_details")
    if isinstance(details, dict):
        raw_reason = details.get("reason")
        if isinstance(raw_reason, str) and raw_reason:
            incomplete_reason = raw_reason[:80]

    raise AgenticResearchError(
        f"OpenAI Responses API returned incomplete response for {stage_name}: "
        f"{incomplete_reason}",
        reason="incomplete_response",
        safe_detail=incomplete_reason,
    )


def _to_strict_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Adapt Pydantic JSON Schema for OpenAI strict structured outputs."""
    strict_schema = deepcopy(schema)
    return _simplify_schema_node(strict_schema)


def _simplify_schema_node(node: Any) -> Any:
    if isinstance(node, list):
        return [_simplify_schema_node(item) for item in node]
    if not isinstance(node, dict):
        return node

    simplified: dict[str, Any] = {}
    for key, value in node.items():
        if key in {"title", "default"}:
            continue
        simplified[key] = _simplify_schema_node(value)

    properties = simplified.get("properties")
    if isinstance(properties, dict):
        simplified["additionalProperties"] = False
        simplified["required"] = list(properties.keys())

    if (
        simplified.get("type") == "object"
        and "additionalProperties" not in simplified
    ):
        simplified["additionalProperties"] = False

    return simplified
