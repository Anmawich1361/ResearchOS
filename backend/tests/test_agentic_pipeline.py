import time
import unittest
from unittest.mock import patch

from app.agentic.config import AgenticResearchConfig
from app.agentic.diagnostics import (
    get_agentic_diagnostics,
    reset_agentic_diagnostics,
)
from app.agentic.openai_client import AgenticResearchError
from app.agentic.pipeline import run_agentic_research_pipeline
from app.agentic.prompts import (
    FRAMEWORK_PROMPT,
    FAST_SYNTHESIS_PROMPT,
    SKEPTIC_PROMPT,
    SOURCE_RESEARCH_PROMPT,
    SYNTHESIS_PROMPT,
)
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN
from app.schemas import ResearchRunRequest


CUSTOM_QUESTION = "How would tariff shocks affect US industrial margins?"
TARGET_QUESTION = "How would a stronger US dollar affect semiconductor earnings?"


class AgenticPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        reset_agentic_diagnostics()

    def test_disabled_mode_returns_deterministic_fallback(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=False, api_key=None),
            client=_FailingClient(),
        )

        self.assertEqual(run.question, CUSTOM_QUESTION)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "config_unavailable",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "config")

    def test_missing_api_key_returns_deterministic_fallback(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key=None),
            client=_FailingClient(),
        )

        self.assertEqual(run.question, CUSTOM_QUESTION)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_forbidden_question_falls_back_before_openai_client(self) -> None:
        questions = [
            "Should I buy Nvidia?",
            "What is the price target for RY?",
            "What's your target price on RY?",
            "Give me a PT for Nvidia.",
            "How much of my portfolio should I put in Nvidia?",
        ]

        for question in questions:
            with self.subTest(question=question):
                with patch(
                    "app.agentic.pipeline.OpenAIResearchClient"
                ) as research_client:
                    run = run_agentic_research_pipeline(
                        ResearchRunRequest(question=question),
                        config=_config(
                            enabled=True,
                            api_key="test-openai-key",
                        ),
                    )

                research_client.assert_not_called()
                self.assertEqual(run.question, question)
                self.assertEqual(
                    run.scenario,
                    CANADIAN_BANKS_RESEARCH_RUN.scenario,
                )

    def test_mocked_valid_agentic_output_returns_research_run(self) -> None:
        valid_run = _valid_agentic_run()
        client = _FakeClient(_valid_stage_responses(valid_run))

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(
                enabled=True,
                api_key="test-openai-key",
                web_search_enabled=True,
            ),
            client=client,
        )

        self.assertEqual(run.question, CUSTOM_QUESTION)
        self.assertEqual(run.scenario, "Agentic beta macro transmission")
        self.assertEqual(
            client.stage_names,
            [
                "agentic_planner",
                "agentic_source_research",
                "agentic_framework",
                "agentic_skeptic",
                "agentic_synthesis",
            ],
        )

    def test_target_prompt_completes_through_fast_path_without_timeout(
        self,
    ) -> None:
        client = _FakeClient(_valid_fast_synthesis_response())

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=TARGET_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=client,
        )

        self.assertEqual(run.question, TARGET_QUESTION)
        self.assertEqual(run.scenario, "Agentic beta fast macro transmission")
        self.assertEqual(client.stage_names, ["agentic_fast_synthesis"])
        self.assertFalse(any(item.type == "Data" for item in run.evidence))
        self.assertFalse(
            any(node.evidenceType == "Data" for node in run.transmissionNodes)
        )
        diagnostics = get_agentic_diagnostics()
        self.assertIsNone(diagnostics["lastFallbackReason"])
        self.assertIsNone(diagnostics["lastFallbackStage"])
        self.assertIsNone(diagnostics["lastErrorType"])
        self.assertIsNotNone(diagnostics["lastSucceededAt"])

    def test_stage_prompts_do_not_instruct_agentic_data_evidence(self) -> None:
        prompts = [
            SOURCE_RESEARCH_PROMPT,
            FRAMEWORK_PROMPT,
            SKEPTIC_PROMPT,
            SYNTHESIS_PROMPT,
            FAST_SYNTHESIS_PROMPT,
        ]
        allowed_labels = [
            "Source claim",
            "Framework inference",
            "Narrative signal",
            "Open question",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt[:24]):
                flattened_prompt = " ".join(prompt.split())
                self.assertIn("Do not use Data", prompt)
                for label in allowed_labels:
                    if prompt == FAST_SYNTHESIS_PROMPT and label == "Source claim":
                        continue
                    self.assertIn(label, flattened_prompt)

    def test_fast_path_timeout_falls_back(self) -> None:
        delay_seconds = 0.5
        client = _SlowStageClient(
            _valid_fast_synthesis_response(),
            slow_stage="agentic_fast_synthesis",
            delay_seconds=delay_seconds,
        )

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=TARGET_QUESTION),
                config=_config(
                    enabled=True,
                    api_key="test-openai-key",
                    pipeline_timeout_seconds=0.01,
                ),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "pipeline_timeout")
        self.assertEqual(diagnostics["lastFallbackStage"], "pipeline")
        self.assertEqual(diagnostics["lastErrorType"], "TimeoutError")
        time.sleep(delay_seconds + 0.02)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "pipeline_timeout")
        self.assertEqual(diagnostics["lastFallbackStage"], "pipeline")

    def test_fast_path_invalid_output_falls_back(self) -> None:
        client = _FakeClient({"agentic_fast_synthesis": {"not": "valid"}})

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=TARGET_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "normalization_failed",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "normalization")

    def test_fast_path_unsafe_output_falls_back(self) -> None:
        response = _valid_fast_synthesis_response(
            headline="Investors should buy the stock."
        )
        client = _FakeClient(response)

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=TARGET_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "safety_failed")
        self.assertEqual(diagnostics["lastFallbackStage"], "safety")

    def test_fast_path_data_evidence_falls_back(self) -> None:
        response = _valid_fast_synthesis_response()
        response["agentic_fast_synthesis"]["evidence"][0]["type"] = "Data"
        client = _FakeClient(response)

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=TARGET_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "normalization_failed",
        )

    def test_source_stage_receives_web_search_disabled_context(self) -> None:
        client = _FakeClient(_valid_stage_responses(_valid_agentic_run()))

        run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=client,
        )

        source_request = client.requests[1]
        source_input = source_request["input_data"]
        self.assertEqual(source_request["stage_name"], "agentic_source_research")
        self.assertIs(source_request["allow_web_search"], False)
        self.assertEqual(source_input["webSearchEnabled"], False)
        self.assertEqual(source_input["sourceMode"], "framework_only")

    def test_pipeline_timeout_falls_back_with_safe_diagnostics(self) -> None:
        delay_seconds = 0.5
        client = _SlowStageClient(
            _valid_stage_responses(_valid_agentic_run()),
            slow_stage="agentic_planner",
            delay_seconds=delay_seconds,
        )

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            start_time = time.monotonic()
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(
                    enabled=True,
                    api_key="test-openai-key",
                    pipeline_timeout_seconds=0.01,
                ),
                client=client,
            )
            elapsed = time.monotonic() - start_time

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        self.assertLess(elapsed, 0.25)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "pipeline_timeout",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "pipeline")
        self.assertEqual(
            diagnostics["lastErrorType"],
            "TimeoutError",
        )
        time.sleep(delay_seconds + 0.02)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "pipeline_timeout",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "pipeline")
        self.assertEqual(
            diagnostics["lastErrorType"],
            "TimeoutError",
        )

    def test_stale_timed_out_worker_cannot_overwrite_newer_diagnostics(
        self,
    ) -> None:
        delay_seconds = 0.5
        client = _SlowStageClient(
            _valid_stage_responses(_valid_agentic_run()),
            slow_stage="agentic_planner",
            delay_seconds=delay_seconds,
        )

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(
                    enabled=True,
                    api_key="test-openai-key",
                    pipeline_timeout_seconds=0.01,
                ),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        self.assertEqual(
            get_agentic_diagnostics()["lastFallbackReason"],
            "pipeline_timeout",
        )

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=False, api_key=None),
            client=_FailingClient(),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "config_unavailable",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "config")
        self.assertIsNone(diagnostics["lastErrorType"])

        time.sleep(delay_seconds + 0.02)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "config_unavailable",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "config")
        self.assertIsNone(diagnostics["lastErrorType"])

    def test_malformed_agentic_output_falls_back(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_framework"] = {"not": "valid"}

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(responses),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_planner_failure_records_fallback_reason(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_planner"] = {"not": "valid"}

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=_FakeClient(responses),
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "planner_failed")
        self.assertEqual(diagnostics["lastFallbackStage"], "planner")
        self.assertEqual(diagnostics["lastErrorType"], "AgenticPipelineError")

    def test_planner_openai_error_records_specific_reason(self) -> None:
        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=_ErrorClient(
                    AgenticResearchError(
                        "OpenAI Responses API returned invalid JSON",
                        reason="invalid_json",
                    )
                ),
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "invalid_json")
        self.assertEqual(diagnostics["lastFallbackStage"], "planner")
        self.assertEqual(diagnostics["lastErrorType"], "AgenticResearchError")

    def test_source_research_openai_error_records_specific_stage(
        self,
    ) -> None:
        client = _StageErrorClient(
            _valid_stage_responses(_valid_agentic_run()),
            error_stage="agentic_source_research",
            error=AgenticResearchError(
                "OpenAI Responses API returned invalid JSON",
                reason="invalid_json",
            ),
        )

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=client,
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "invalid_json")
        self.assertEqual(diagnostics["lastFallbackStage"], "source_research")
        self.assertEqual(diagnostics["lastErrorType"], "AgenticResearchError")

    def test_malformed_synthesis_records_normalization_stage(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_synthesis"] = {"not": "valid"}

        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(enabled=True, api_key="test-openai-key"),
                client=_FakeClient(responses),
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(
            diagnostics["lastFallbackReason"],
            "normalization_failed",
        )
        self.assertEqual(diagnostics["lastFallbackStage"], "normalization")

    def test_out_of_scope_planner_output_falls_back(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_planner"] = {
            **responses["agentic_planner"],
            "scope": "out_of_scope",
            "rejectedReason": "Requests a price target.",
        }

        run = run_agentic_research_pipeline(
            ResearchRunRequest(
                question="What valuation sensitivities matter for RY?"
            ),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(responses),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_forbidden_price_target_output_falls_back(self) -> None:
        invalid_run = _valid_agentic_run(
            thesis="This output includes a price target."
        )

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(_valid_stage_responses(invalid_run)),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_forbidden_buy_recommendation_output_falls_back(self) -> None:
        invalid_run = _valid_agentic_run(
            headline="Investors should buy the stock."
        )

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(_valid_stage_responses(invalid_run)),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_evidence_labels_remain_restricted(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(
                enabled=True,
                api_key="test-openai-key",
                web_search_enabled=True,
            ),
            client=_FakeClient(_valid_stage_responses(_valid_agentic_run())),
        )

        self.assertLessEqual(
            {item.type for item in run.evidence},
            {
                "Data",
                "Source claim",
                "Framework inference",
                "Narrative signal",
                "Open question",
            },
        )

    def test_data_evidence_falls_back_when_model_output_uses_data(self) -> None:
        with self.assertLogs("app.agentic.pipeline", level="WARNING"):
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question=CUSTOM_QUESTION),
                config=_config(
                    enabled=True,
                    api_key="test-openai-key",
                    web_search_enabled=True,
                ),
                client=_FakeClient(
                    _valid_stage_responses(
                        _valid_agentic_run(include_data_evidence=True)
                    )
                ),
            )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        diagnostics = get_agentic_diagnostics()
        self.assertEqual(diagnostics["lastFallbackReason"], "safety_failed")
        self.assertEqual(diagnostics["lastFallbackStage"], "safety")

    def test_model_source_notes_cannot_authorize_data_evidence(
        self,
    ) -> None:
        spoofed_label = "Fake Official Source"
        responses = _valid_stage_responses(
            _valid_agentic_run(
                include_data_evidence=True,
                data_source_label=spoofed_label,
            )
        )
        responses["agentic_source_research"]["sourceNotes"][0]["sourceLabel"] = (
            spoofed_label
        )

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(
                enabled=True,
                api_key="test-openai-key",
                web_search_enabled=True,
            ),
            client=_FakeClient(responses),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_unrelated_agentic_fallback_does_not_leak_boc_marker(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=False, api_key=None),
            client=_FailingClient(),
        )

        self.assertFalse(
            any(
                item.sourceLabel == "Bank of Canada Valet API"
                for item in run.evidence
            )
        )


class _FakeClient:
    def __init__(self, responses: dict[str, dict[str, object]]) -> None:
        self._responses = responses
        self.stage_names: list[str] = []
        self.requests: list[dict[str, object]] = []

    def create_structured_response(self, **kwargs: object) -> dict[str, object]:
        stage_name = str(kwargs["stage_name"])
        self.stage_names.append(stage_name)
        self.requests.append(kwargs)
        return self._responses[stage_name]


class _FailingClient:
    def create_structured_response(self, **_: object) -> dict[str, object]:
        raise AssertionError("OpenAI client should not be called")


class _ErrorClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def create_structured_response(self, **_: object) -> dict[str, object]:
        raise self._error


class _StageErrorClient(_FakeClient):
    def __init__(
        self,
        responses: dict[str, dict[str, object]],
        *,
        error_stage: str,
        error: Exception,
    ) -> None:
        super().__init__(responses)
        self._error_stage = error_stage
        self._error = error

    def create_structured_response(self, **kwargs: object) -> dict[str, object]:
        stage_name = str(kwargs["stage_name"])
        if stage_name == self._error_stage:
            self.stage_names.append(stage_name)
            self.requests.append(kwargs)
            raise self._error
        return super().create_structured_response(**kwargs)


class _SlowStageClient(_FakeClient):
    def __init__(
        self,
        responses: dict[str, dict[str, object]],
        *,
        slow_stage: str,
        delay_seconds: float,
    ) -> None:
        super().__init__(responses)
        self._slow_stage = slow_stage
        self._delay_seconds = delay_seconds

    def create_structured_response(self, **kwargs: object) -> dict[str, object]:
        stage_name = str(kwargs["stage_name"])
        if stage_name == self._slow_stage:
            time.sleep(self._delay_seconds)
        return super().create_structured_response(**kwargs)


def _config(
    *,
    enabled: bool,
    api_key: str | None,
    web_search_enabled: bool = False,
    pipeline_timeout_seconds: float = 45.0,
) -> AgenticResearchConfig:
    return AgenticResearchConfig(
        enabled=enabled,
        api_key=api_key,
        model="gpt-5.4-mini",
        web_search_enabled=web_search_enabled,
        timeout_seconds=1.0,
        pipeline_timeout_seconds=pipeline_timeout_seconds,
        max_output_tokens=4000,
        reasoning_effort="minimal",
    )


def _valid_agentic_run(
    *,
    question: str = CUSTOM_QUESTION,
    headline: str | None = None,
    thesis: str | None = None,
    include_data_evidence: bool = False,
    data_source_label: str = "US Census Bureau",
):
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
        deep=True,
        update={
            "question": question,
            "timestamp": "Agentic beta run | mocked",
            "scenario": "Agentic beta macro transmission",
            "headline": headline
            or (
                "Tariff shocks can pressure industrial margins through input "
                "costs, pricing power, and working-capital timing."
            ),
            "thesis": thesis
            or (
                "The tariff setup is analytically mixed. Margin pressure "
                "depends on cost pass-through, customer elasticity, supplier "
                "contracts, and inventory timing."
            ),
        },
    )
    for item in run.evidence:
        if item.type == "Data":
            item.sourceLabel = data_source_label
            item.sourceType = "Official trade data"
            item.sourceQuality = "High"
            if not include_data_evidence:
                item.type = "Source claim"
    if not include_data_evidence:
        for node in run.transmissionNodes:
            if node.evidenceType == "Data":
                node.evidenceType = "Source claim"
    return run


def _valid_stage_responses(run) -> dict[str, dict[str, object]]:
    return {
        "agentic_planner": {
            "researchType": "macro_to_sector_shock",
            "shock": "tariff shock",
            "affectedEntities": ["US industrials"],
            "drivers": [
                "Input costs",
                "Pricing power",
                "Supplier contracts",
                "Inventory timing",
            ],
            "scope": "in_scope",
            "researchObjective": (
                "Map tariff transmission into industrial margins."
            ),
            "rejectedReason": None,
        },
        "agentic_source_research": {
            "sourceNotes": [
                {
                    "sourceLabel": "US Census Bureau",
                    "sourceType": "Official trade data",
                    "sourceQuality": "High",
                    "claim": "Trade exposures vary by product category.",
                    "relevance": "Frames the tariff exposure map.",
                    "openQuestions": ["Which categories face the shock?"],
                }
            ],
            "openQuestions": ["Which supplier contracts reset first?"],
        },
        "agentic_framework": {
            "transmissionNodes": [
                node.model_dump() for node in run.transmissionNodes
            ],
            "transmissionEdges": [
                edge.model_dump() for edge in run.transmissionEdges
            ],
            "evidence": [item.model_dump() for item in run.evidence],
        },
        "agentic_skeptic": {
            "bearCase": run.bearCase.model_dump(),
            "openQuestions": [
                question.model_dump() for question in run.openQuestions
            ],
            "evidence": [item.model_dump() for item in run.evidence],
        },
        "agentic_synthesis": {
            "researchRun": run.model_dump(),
        },
    }


def _valid_fast_synthesis_response(
    *,
    headline: str | None = None,
) -> dict[str, dict[str, object]]:
    return {
        "agentic_fast_synthesis": {
            "researchType": "macro_to_sector_shock",
            "shock": "stronger US dollar",
            "affectedEntities": [
                "semiconductor manufacturers",
                "semiconductor equipment suppliers",
            ],
            "headline": headline
            or (
                "A stronger dollar can pressure semiconductor earnings "
                "through translation, demand, mix, and inventory channels."
            ),
            "thesis": (
                "The dollar shock is a conditional earnings headwind. The "
                "largest analytical questions are foreign-revenue translation, "
                "customer purchasing power, pricing offsets, and whether "
                "inventory corrections amplify the FX move."
            ),
            "keyDrivers": [
                "Foreign-revenue translation",
                "Export demand sensitivity",
                "Gross-margin mix",
                "Inventory and order timing",
            ],
            "transmission": [
                {
                    "label": "Dollar shock",
                    "subtitle": "USD strengthens versus customer currencies",
                    "driver": "FX translation",
                    "evidenceType": "Framework inference",
                    "confidence": "Medium",
                    "researchImplication": (
                        "Separate reported revenue translation from constant "
                        "currency demand."
                    ),
                    "whyItMatters": (
                        "Semiconductor revenue is global, so currency moves "
                        "can change reported growth even when units are stable."
                    ),
                    "polarity": "negative",
                },
                {
                    "label": "Demand channel",
                    "subtitle": "Non-US customers face purchasing-power pressure",
                    "driver": "Export demand",
                    "evidenceType": "Framework inference",
                    "confidence": "Medium",
                    "researchImplication": (
                        "Test whether customers defer orders or trade down."
                    ),
                    "whyItMatters": (
                        "A currency shock can look like softer end demand if "
                        "local-currency budgets tighten."
                    ),
                    "polarity": "risk",
                },
                {
                    "label": "Margin channel",
                    "subtitle": "Pricing, cost base, and mix determine offset",
                    "driver": "Gross margin",
                    "evidenceType": "Framework inference",
                    "confidence": "Medium",
                    "researchImplication": (
                        "Compare pricing power with geographic and product mix."
                    ),
                    "whyItMatters": (
                        "High-value chips may offset FX pressure better than "
                        "more commoditized exposure."
                    ),
                    "polarity": "mixed",
                },
                {
                    "label": "Earnings quality",
                    "subtitle": "Inventory and guidance risk shape interpretation",
                    "driver": "Order timing",
                    "evidenceType": "Open question",
                    "confidence": "Medium",
                    "researchImplication": (
                        "Watch whether FX effects coincide with inventory "
                        "digestion or customer pushouts."
                    ),
                    "whyItMatters": (
                        "The same currency shock is more consequential if it "
                        "arrives during a cyclical order slowdown."
                    ),
                    "polarity": "risk",
                },
            ],
            "evidence": [
                {
                    "claim": (
                        "Reported semiconductor revenue can diverge from "
                        "constant-currency demand when the dollar strengthens."
                    ),
                    "type": "Framework inference",
                    "confidence": "Medium",
                    "importance": "High",
                    "driver": "FX translation",
                    "sourceLabel": "Framework-only synthesis",
                    "sourceType": "Agentic framework inference",
                    "sourceQuality": "Medium",
                },
                {
                    "claim": (
                        "Pricing power and product mix can partly offset "
                        "currency pressure, but the offset is company-specific."
                    ),
                    "type": "Framework inference",
                    "confidence": "Medium",
                    "importance": "High",
                    "driver": "Gross margin",
                    "sourceLabel": "Framework-only synthesis",
                    "sourceType": "Agentic framework inference",
                    "sourceQuality": "Medium",
                },
                {
                    "claim": (
                        "A dollar shock is harder to interpret when inventory "
                        "digestion and order pushouts are also present."
                    ),
                    "type": "Open question",
                    "confidence": "Medium",
                    "importance": "Medium",
                    "driver": "Order timing",
                    "sourceLabel": "Framework-only synthesis",
                    "sourceType": "Agentic open question",
                    "sourceQuality": "Low",
                },
            ],
            "bullCaseTitle": "What could cushion the shock",
            "bullCasePoints": [
                "High pricing power and differentiated products reduce FX pass-through.",
                "US-dollar cost structures can offset part of translation pressure.",
            ],
            "bearCaseTitle": "What could amplify the shock",
            "bearCasePoints": [
                "Local-currency customer budgets weaken at the same time reported revenue translates lower.",
                "Inventory corrections make FX pressure look like broader demand weakness.",
            ],
            "memoSections": [
                {
                    "title": "Transmission view",
                    "body": (
                        "A stronger dollar first affects reported revenue "
                        "translation, then customer purchasing power, then "
                        "margin interpretation."
                    ),
                },
                {
                    "title": "Evidence posture",
                    "body": (
                        "This beta output is framework-only and does not use "
                        "independently verified Data evidence."
                    ),
                },
                {
                    "title": "Research next steps",
                    "body": (
                        "Separate constant-currency revenue, geographic mix, "
                        "pricing power, and inventory indicators before "
                        "forming company-specific conclusions."
                    ),
                },
            ],
            "openQuestions": [
                {
                    "question": (
                        "How much revenue is exposed to non-US customer "
                        "currencies?"
                    ),
                    "whyItMatters": (
                        "It separates translation risk from underlying unit "
                        "demand."
                    ),
                    "owner": "Source research",
                },
                {
                    "question": (
                        "Are inventory corrections already visible in orders "
                        "or guidance?"
                    ),
                    "whyItMatters": (
                        "Inventory pressure could amplify the earnings impact "
                        "of a currency shock."
                    ),
                    "owner": "Skeptic",
                },
            ],
        }
    }


if __name__ == "__main__":
    unittest.main()
