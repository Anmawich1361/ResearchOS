import json
from copy import deepcopy
from http import HTTPStatus
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
            raise AgenticResearchError(
                "OpenAI API key is not configured",
                reason="config_unavailable",
            )
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
        except HTTPError as exc:
            reason = _classify_http_error(exc)
            raise AgenticResearchError(
                f"OpenAI Responses API HTTP error for {stage_name}",
                reason=reason,
                safe_detail=_safe_http_detail(exc, reason),
            ) from exc
        except URLError as exc:
            raise AgenticResearchError(
                f"OpenAI Responses API URL error for {stage_name}",
                reason="url_error",
                safe_detail=type(exc.reason).__name__,
            ) from exc
        except TimeoutError as exc:
            raise AgenticResearchError(
                f"OpenAI Responses API timeout for {stage_name}",
                reason="timeout",
                safe_detail=type(exc).__name__,
            ) from exc
        except json.JSONDecodeError as exc:
            raise AgenticResearchError(
                "OpenAI Responses API returned invalid response JSON "
                f"for {stage_name}",
                reason="response_error",
                safe_detail="invalid_response_json",
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
    error_message = ""
    if isinstance(error, dict):
        raw_type = error.get("type") or error.get("code")
        if isinstance(raw_type, str) and raw_type:
            error_type = raw_type[:80]
        raw_message = error.get("message")
        if isinstance(raw_message, str):
            error_message = raw_message
    elif isinstance(error, str):
        error_type = error[:80]
        error_message = error

    reason = (
        "schema_rejected"
        if _looks_like_schema_rejection(error_type, error_message)
        else "response_error"
    )

    raise AgenticResearchError(
        f"OpenAI Responses API returned an error for {stage_name}: "
        f"{error_type}",
        reason=reason,
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

    simplified = _collapse_simple_any_of(simplified)

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


def _collapse_simple_any_of(node: dict[str, Any]) -> dict[str, Any]:
    any_of = node.get("anyOf")
    if not isinstance(any_of, list):
        return node

    types: list[str] = []
    for option in any_of:
        if not isinstance(option, dict):
            return node
        option_type = option.get("type")
        if not isinstance(option_type, str):
            return node
        unsupported_keys = set(option) - {"type"}
        if unsupported_keys:
            return node
        types.append(option_type)

    if not types:
        return node

    collapsed = dict(node)
    collapsed.pop("anyOf", None)
    collapsed["type"] = list(dict.fromkeys(types))
    return collapsed


def _classify_http_error(exc: HTTPError) -> str:
    error_body = _read_http_error_body(exc)
    if _looks_like_schema_rejection(str(exc.code), error_body):
        return "schema_rejected"
    return "http_error"


def _safe_http_detail(exc: HTTPError, reason: str) -> str:
    if reason == "schema_rejected":
        return "schema_rejected"
    try:
        phrase = HTTPStatus(exc.code).phrase.lower().replace(" ", "_")
    except ValueError:
        phrase = "http_error"
    return f"http_{exc.code}_{phrase}"[:80]


def _read_http_error_body(exc: HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", errors="replace")[:4000]
    except Exception:
        return ""


def _looks_like_schema_rejection(error_type: str, message: str) -> bool:
    text = f"{error_type} {message}".lower()
    return (
        "schema" in text
        or "json_schema" in text
        or "response_format" in text
        or "strict" in text
    )
