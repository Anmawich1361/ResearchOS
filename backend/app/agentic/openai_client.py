import json
from copy import deepcopy
from http import HTTPStatus
from typing import Any

from app.agentic.config import AgenticResearchConfig
from app.agentic.prompts import AGENTIC_SYSTEM_INSTRUCTIONS


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
    def __init__(
        self,
        config: AgenticResearchConfig,
        *,
        sdk_client: Any | None = None,
    ) -> None:
        if not config.api_key:
            raise AgenticResearchError(
                "OpenAI API key is not configured",
                reason="config_unavailable",
            )
        self._config = config
        self._client = sdk_client or _create_openai_sdk_client(config)

    def create_structured_response(
        self,
        *,
        stage_name: str,
        instructions: str,
        schema: dict[str, Any],
        input_data: dict[str, Any],
        allow_web_search: bool = False,
        request_timeout_seconds: float | None = None,
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

        if request_timeout_seconds is not None:
            payload["timeout"] = request_timeout_seconds

        try:
            response = self._client.responses.create(**payload)
        except Exception as exc:
            reason = _classify_sdk_error(exc)
            raise AgenticResearchError(
                f"OpenAI Responses API request failed for {stage_name}",
                reason=reason,
                safe_detail=_safe_sdk_detail(exc, reason),
            ) from exc

        response_payload = _response_to_payload(response)
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


def _create_openai_sdk_client(config: AgenticResearchConfig) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AgenticResearchError(
            "OpenAI SDK is not installed",
            reason="config_unavailable",
            safe_detail="openai_sdk_unavailable",
        ) from exc

    return OpenAI(
        api_key=config.api_key,
        timeout=config.timeout_seconds,
    )


def _response_to_payload(response: Any) -> dict[str, Any]:
    if isinstance(response, dict):
        payload = dict(response)
    elif hasattr(response, "model_dump"):
        payload = response.model_dump(mode="python")
    elif hasattr(response, "to_dict"):
        payload = response.to_dict()
    elif hasattr(response, "dict"):
        payload = response.dict()
    else:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and not isinstance(
        payload.get("output_text"),
        str,
    ):
        payload["output_text"] = output_text

    for field in ("status", "error", "incomplete_details", "output"):
        if field not in payload and hasattr(response, field):
            payload[field] = getattr(response, field)

    return payload


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
        error_type = _safe_error_type(error)
        raw_message = error.get("message")
        if isinstance(raw_message, str):
            error_message = raw_message
    elif isinstance(error, str):
        error_type = error[:80]
        error_message = error
    else:
        error_type = _safe_error_type(error)
        raw_message = getattr(error, "message", None)
        if isinstance(raw_message, str):
            error_message = raw_message

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
    elif details is not None:
        raw_reason = getattr(details, "reason", None)
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


def _classify_sdk_error(exc: Exception) -> str:
    names = _exception_class_names(exc)
    cause_names = _exception_cause_class_names(exc)
    name = type(exc).__name__
    text = _safe_exception_text(exc)
    status_code = getattr(exc, "status_code", None)

    if (
        "APITimeoutError" in names
        or any("Timeout" in cause_name for cause_name in cause_names)
        or "Timeout" in name
        or name == "TimeoutError"
    ):
        return "timeout"
    if isinstance(exc, TimeoutError):
        return "timeout"
    if (
        "APIConnectionError" in names
        or any(
            cause_name
            in {
                "ConnectError",
                "ConnectionError",
                "NetworkError",
                "ReadError",
                "RemoteProtocolError",
                "URLError",
            }
            for cause_name in cause_names
        )
        or "ConnectionError" in name
        or name in {"URLError", "ConnectError"}
    ):
        return "url_error"
    if "BadRequestError" in names and _looks_like_schema_rejection(name, text):
        return "schema_rejected"
    if "APIResponseValidationError" in names:
        return "response_error"
    if name == "APIError":
        return "response_error"
    if "APIStatusError" in names or status_code is not None:
        if _looks_like_schema_rejection(str(status_code), text):
            return "schema_rejected"
        return "http_error"
    if "APIError" in names:
        return "response_error"
    if _looks_like_schema_rejection(name, text):
        return "schema_rejected"

    return "response_error"


def _safe_sdk_detail(exc: Exception, reason: str) -> str:
    if reason == "schema_rejected":
        return "schema_rejected"
    if reason == "http_error":
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int):
            try:
                phrase = HTTPStatus(status_code).phrase.lower().replace(" ", "_")
            except ValueError:
                phrase = "http_error"
            return f"http_{status_code}_{phrase}"[:80]
    if reason in {"timeout", "url_error"}:
        cause_name = _safe_cause_class_name(exc)
        if cause_name:
            return cause_name
    return type(exc).__name__[:80]


def _safe_exception_text(exc: Exception) -> str:
    chunks: list[str] = [type(exc).__name__]
    for attr in ("code", "type", "message"):
        value = getattr(exc, attr, None)
        if isinstance(value, str):
            chunks.append(value)

    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            chunks.append(_safe_error_type(error))
            message = error.get("message")
            if isinstance(message, str):
                chunks.append(message[:4000])
        else:
            chunks.append(_safe_json_dump(body))
    elif isinstance(body, str):
        chunks.append(body[:4000])

    response = getattr(exc, "response", None)
    if response is not None:
        try:
            response_json = response.json()
        except Exception:
            response_json = None
        if isinstance(response_json, dict):
            chunks.append(_safe_json_dump(response_json))

    return " ".join(chunks)


def _exception_class_names(exc: Exception) -> set[str]:
    return {cls.__name__ for cls in type(exc).__mro__}


def _exception_cause_class_names(exc: Exception) -> set[str]:
    names: set[str] = set()
    seen: set[int] = set()
    current = exc.__cause__ or exc.__context__
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        names.add(type(current).__name__)
        current = current.__cause__ or current.__context__
    return names


def _safe_cause_class_name(exc: Exception) -> str | None:
    current = exc.__cause__ or exc.__context__
    seen: set[int] = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        name = type(current).__name__
        if name:
            return name[:80]
        current = current.__cause__ or current.__context__
    return None


def _safe_json_dump(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True)[:4000]
    except (TypeError, ValueError):
        return type(value).__name__[:80]


def _safe_error_type(error: Any) -> str:
    if isinstance(error, dict):
        raw_type = error.get("type") or error.get("code")
    else:
        raw_type = getattr(error, "type", None) or getattr(error, "code", None)
    if isinstance(raw_type, str) and raw_type:
        return raw_type[:80]
    return "unknown_error"


def _looks_like_schema_rejection(error_type: str, message: str) -> bool:
    text = f"{error_type} {message}".lower()
    return (
        "schema" in text
        or "json_schema" in text
        or "response_format" in text
        or "text.format" in text
        or "structured output" in text
        or "structured_outputs" in text
        or "strict" in text
    )
