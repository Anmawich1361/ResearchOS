import json
import unittest

from app.agentic.config import AgenticResearchConfig
from app.agentic.models import PlannerStageResult
from app.agentic.openai_client import (
    AgenticResearchError,
    OpenAIResearchClient,
    _to_strict_json_schema,
)


class OpenAIResearchClientTest(unittest.TestCase):
    def test_payload_uses_safe_responses_structured_output_settings(
        self,
    ) -> None:
        payload = _capture_request_payload(web_search_enabled=False)

        self.assertEqual(payload["model"], "gpt-5.4-mini")
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
        self.assertNotIn("tools", payload)
        self.assertNotIn("tool_choice", payload)

    def test_planner_payload_includes_storage_and_token_settings(self) -> None:
        payload = _capture_request_payload(
            web_search_enabled=False,
            stage_name="agentic_planner",
            schema=PlannerStageResult.model_json_schema(),
        )

        self.assertIs(payload["store"], False)
        self.assertEqual(payload["max_output_tokens"], 4000)
        self.assertEqual(payload["text"]["format"]["name"], "agentic_planner")

    def test_planner_schema_is_json_serializable_after_simplification(
        self,
    ) -> None:
        schema = _to_strict_json_schema(PlannerStageResult.model_json_schema())

        json.dumps(schema)
        self.assertEqual(schema["additionalProperties"], False)
        self.assertIn("rejectedReason", schema["required"])
        self.assertEqual(
            schema["properties"]["rejectedReason"]["type"],
            ["string", "null"],
        )
        self.assertNotIn(
            "anyOf",
            schema["properties"]["rejectedReason"],
        )

    def test_source_stage_with_web_search_uses_required_tool_choice(
        self,
    ) -> None:
        payload = _capture_request_payload(web_search_enabled=True)

        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        self.assertEqual(payload["tool_choice"], "required")

    def test_connection_error_maps_to_url_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response_from_sdk(side_effect=_FakeAPIConnectionError())

        self.assertEqual(context.exception.reason, "url_error")
        self.assertEqual(
            context.exception.safe_detail,
            "_FakeAPIConnectionError",
        )

    def test_timeout_error_maps_to_timeout(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response_from_sdk(side_effect=_FakeAPITimeoutError())

        self.assertEqual(context.exception.reason, "timeout")
        self.assertEqual(
            context.exception.safe_detail,
            "_FakeAPITimeoutError",
        )

    def test_api_status_error_maps_to_http_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response_from_sdk(
                side_effect=_FakeAPIStatusError(
                    status_code=503,
                    body={"error": {"type": "server_error"}},
                )
            )

        self.assertEqual(context.exception.reason, "http_error")
        self.assertEqual(
            context.exception.safe_detail,
            "http_503_service_unavailable",
        )

    def test_api_response_error_maps_to_response_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response_from_sdk(
                side_effect=_FakeAPIResponseValidationError()
            )

        self.assertEqual(context.exception.reason, "response_error")
        self.assertEqual(
            context.exception.safe_detail,
            "_FakeAPIResponseValidationError",
        )

    def test_incomplete_response_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(
                _FakeResponse(
                    status="incomplete",
                    incomplete_details={"reason": "max_output_tokens"},
                    output=[],
                )
            )

        self.assertEqual(context.exception.reason, "incomplete_response")
        self.assertEqual(context.exception.safe_detail, "max_output_tokens")

    def test_response_error_field_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(
                _FakeResponse(
                    error={
                        "type": "invalid_request_error",
                        "message": "schema rejected",
                    },
                )
            )

        self.assertEqual(context.exception.reason, "schema_rejected")
        self.assertEqual(context.exception.safe_detail, "invalid_request_error")

    def test_status_schema_rejection_raises_specific_reason_code(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response_from_sdk(
                side_effect=_FakeAPIStatusError(
                    status_code=400,
                    body={
                        "error": {
                            "type": "invalid_request_error",
                            "message": "Invalid schema for response_format.",
                        }
                    },
                )
            )

        self.assertEqual(context.exception.reason, "schema_rejected")
        self.assertEqual(context.exception.safe_detail, "schema_rejected")

    def test_response_with_no_output_text_raises_agentic_research_error(
        self,
    ) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(_FakeResponse(output=[]))

        self.assertEqual(context.exception.reason, "no_output_text")

    def test_invalid_json_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(_FakeResponse(output_text="{not valid json"))

        self.assertEqual(context.exception.reason, "invalid_json")

    def test_non_object_json_raises_agentic_research_error(self) -> None:
        with self.assertRaises(AgenticResearchError) as context:
            _create_response(
                _FakeResponse(output_text=json.dumps(["not", "object"]))
            )

        self.assertEqual(context.exception.reason, "non_object_json")

    def test_valid_output_text_json_parses_successfully(self) -> None:
        parsed = _create_response(
            _FakeResponse(output_text=json.dumps({"ok": True}))
        )

        self.assertEqual(parsed, {"ok": True})

    def test_sdk_output_text_property_overrides_empty_dump_field(self) -> None:
        parsed = _create_response(
            _FakeModelDumpResponse(output_text=json.dumps({"ok": True}))
        )

        self.assertEqual(parsed, {"ok": True})


class _FakeResponse:
    def __init__(
        self,
        *,
        output_text: str | None = None,
        status: str | None = None,
        error: object | None = None,
        incomplete_details: object | None = None,
        output: list[object] | None = None,
    ) -> None:
        self.output_text = output_text
        self.status = status
        self.error = error
        self.incomplete_details = incomplete_details
        self.output = output


class _FakeModelDumpResponse(_FakeResponse):
    def model_dump(self, mode: str) -> dict[str, object | None]:
        self.model_dump_mode = mode
        return {"output_text": None}


class _FakeResponsesEndpoint:
    def __init__(
        self,
        *,
        return_value: _FakeResponse | None = None,
        side_effect: Exception | None = None,
    ) -> None:
        self.return_value = return_value or _FakeResponse(
            output_text=json.dumps({"ok": True})
        )
        self.side_effect = side_effect
        self.payload: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _FakeResponse:
        self.payload = kwargs
        if self.side_effect:
            raise self.side_effect
        return self.return_value


class _FakeSDKClient:
    def __init__(
        self,
        *,
        return_value: _FakeResponse | None = None,
        side_effect: Exception | None = None,
    ) -> None:
        self.responses = _FakeResponsesEndpoint(
            return_value=return_value,
            side_effect=side_effect,
        )


class _FakeAPIConnectionError(Exception):
    pass


class _FakeAPITimeoutError(Exception):
    pass


class _FakeAPIResponseValidationError(Exception):
    pass


class _FakeAPIStatusError(Exception):
    def __init__(self, *, status_code: int, body: object) -> None:
        super().__init__("OpenAI API status error")
        self.status_code = status_code
        self.body = body


def _capture_request_payload(
    *,
    web_search_enabled: bool,
    stage_name: str = "agentic_source_research",
    schema: dict[str, object] | None = None,
) -> dict[str, object]:
    sdk_client = _FakeSDKClient()

    client = OpenAIResearchClient(
        AgenticResearchConfig(
            enabled=True,
            api_key="test-openai-key",
            model="gpt-5.4-mini",
            web_search_enabled=web_search_enabled,
            timeout_seconds=1.0,
            max_output_tokens=4000,
            reasoning_effort="minimal",
        ),
        sdk_client=sdk_client,
    )

    client.create_structured_response(
        stage_name=stage_name,
        instructions="Return JSON.",
        schema=schema or {"type": "object"},
        input_data={"question": "How do tariffs affect margins?"},
        allow_web_search=True,
    )

    assert sdk_client.responses.payload is not None
    return sdk_client.responses.payload


def _create_response(response: _FakeResponse) -> dict[str, object]:
    return _create_response_from_sdk(
        return_value=response,
    )


def _create_response_from_sdk(
    *,
    return_value: _FakeResponse | None = None,
    side_effect: Exception | None = None,
) -> dict[str, object]:
    sdk_client = _FakeSDKClient(
        return_value=return_value,
        side_effect=side_effect,
    )
    client = OpenAIResearchClient(
        AgenticResearchConfig(
            enabled=True,
            api_key="test-openai-key",
            model="gpt-5",
            web_search_enabled=False,
            timeout_seconds=1.0,
            max_output_tokens=4000,
            reasoning_effort="minimal",
        ),
        sdk_client=sdk_client,
    )

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
