import json
import unittest
from unittest.mock import patch

from app.agentic.config import AgenticResearchConfig
from app.agentic.openai_client import OpenAIResearchClient


class OpenAIResearchClientTest(unittest.TestCase):
    def test_payload_disables_response_storage(self) -> None:
        payload = _capture_request_payload(web_search_enabled=False)

        self.assertIs(payload["store"], False)

    def test_source_stage_with_web_search_uses_required_tool_choice(
        self,
    ) -> None:
        payload = _capture_request_payload(web_search_enabled=True)

        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        self.assertEqual(payload["tool_choice"], "required")


class _FakeResponse:
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {"output_text": json.dumps({"ok": True})}
        ).encode("utf-8")


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


if __name__ == "__main__":
    unittest.main()
