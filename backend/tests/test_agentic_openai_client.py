import json
import unittest
from unittest.mock import patch

from app.agentic.config import AgenticResearchConfig
from app.agentic.openai_client import AgenticResearchError, OpenAIResearchClient


class OpenAIResearchClientTest(unittest.TestCase):
    def test_payload_uses_safe_responses_structured_output_settings(
        self,
    ) -> None:
        payload = _capture_request_payload(web_search_enabled=False)

        self.assertIs(payload["store"], False)
        self.assertEqual(payload["max_output_tokens"], 4000)
        self.assertEqual(payload["reasoning"], {"effort": "minimal"})
        self.assertEqual(
            payload["text"]["format"]["type"],
            "json_schema",
        )
        self.assertIs(payload["text"]["format"]["strict"], True)
        self.assertEqual(
            payload["text"]["format"]["schema"]["additionalProperties"],
            False,
        )

    def test_source_stage_with_web_search_uses_required_tool_choice(
        self,
    ) -> None:
        payload = _capture_request_payload(web_search_enabled=True)

        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        self.assertEqual(payload["tool_choice"], "required")

    def test_incomplete_response_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(
                {
                    "status": "incomplete",
                    "incomplete_details": {"reason": "max_output_tokens"},
                    "output": [],
                }
            )

        self.assertEqual(context.exception.reason, "incomplete_response")
        self.assertEqual(context.exception.safe_detail, "max_output_tokens")

    def test_response_error_field_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(
                {
                    "error": {
                        "type": "invalid_request_error",
                        "message": "schema rejected",
                    }
                }
            )

        self.assertEqual(context.exception.reason, "api_error")
        self.assertEqual(context.exception.safe_detail, "invalid_request_error")

    def test_response_with_no_output_text_raises_agentic_research_error(
        self,
    ) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response({"output": []})

        self.assertEqual(context.exception.reason, "no_output_text")

    def test_valid_output_text_json_parses_successfully(self) -> None:
        parsed = _create_response({"output_text": json.dumps({"ok": True})})

        self.assertEqual(parsed, {"ok": True})


class _FakeResponse:
    def __init__(self, payload: dict[str, object] | None = None) -> None:
        self._payload = payload or {"output_text": json.dumps({"ok": True})}

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _capture_request_payload(*, web_search_enabled: bool) -> dict[str, object]:
    captured_payload: dict[str, object] = {}

    def fake_urlopen(request, timeout):
        del timeout
        assert request.data is not None
        captured_payload.update(
            json.loads(request.data.decode("utf-8"))
        )
        return _FakeResponse()

    client = OpenAIResearchClient(
        AgenticResearchConfig(
            enabled=True,
            api_key="test-openai-key",
            model="gpt-5.4-mini",
            web_search_enabled=web_search_enabled,
            timeout_seconds=1.0,
            max_output_tokens=4000,
            reasoning_effort="minimal",
        )
    )

    with patch("app.agentic.openai_client.urlopen", side_effect=fake_urlopen):
        client.create_structured_response(
            stage_name="agentic_source_research",
            instructions="Return JSON.",
            schema={"type": "object"},
            input_data={"question": "How do tariffs affect margins?"},
            allow_web_search=True,
        )

    return captured_payload


def _create_response(response_payload: dict[str, object]) -> dict[str, object]:
    client = OpenAIResearchClient(
        AgenticResearchConfig(
            enabled=True,
            api_key="test-openai-key",
            model="gpt-5",
            web_search_enabled=False,
            timeout_seconds=1.0,
            max_output_tokens=4000,
            reasoning_effort="minimal",
        )
    )

    with patch(
        "app.agentic.openai_client.urlopen",
        return_value=_FakeResponse(response_payload),
    ):
        return client.create_structured_response(
            stage_name="agentic_planner",
            instructions="Return JSON.",
            schema={
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
            },
            input_data={"question": "How do tariffs affect margins?"},
        )


if __name__ == "__main__":
    unittest.main()
