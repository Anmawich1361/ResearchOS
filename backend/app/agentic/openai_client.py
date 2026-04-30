import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.agentic.config import AgenticResearchConfig
from app.agentic.prompts import AGENTIC_SYSTEM_INSTRUCTIONS


RESPONSES_API_URL = "https://api.openai.com/v1/responses"


class AgenticResearchError(RuntimeError):
    pass


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
                    "strict": False,
                    "schema": schema,
                }
            },
            "reasoning": {"effort": "low"},
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
                f"OpenAI Responses API request failed for {stage_name}"
            ) from exc

        output_text = _extract_output_text(response_payload)
        if not output_text:
            raise AgenticResearchError(
                f"OpenAI Responses API returned no text for {stage_name}"
            )

        try:
            parsed = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise AgenticResearchError(
                f"OpenAI Responses API returned invalid JSON for {stage_name}"
            ) from exc

        if not isinstance(parsed, dict):
            raise AgenticResearchError(
                f"OpenAI Responses API returned non-object JSON for {stage_name}"
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
