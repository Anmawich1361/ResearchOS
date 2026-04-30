import unittest
from unittest.mock import patch

from app.agentic.config import AgenticResearchConfig
from app.agentic.pipeline import run_agentic_research_pipeline
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN
from app.schemas import ResearchRunRequest


CUSTOM_QUESTION = "How would tariff shocks affect US industrial margins?"


class AgenticPipelineTest(unittest.TestCase):
    def test_disabled_mode_returns_deterministic_fallback(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=False, api_key=None),
            client=_FailingClient(),
        )

        self.assertEqual(run.question, CUSTOM_QUESTION)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_missing_api_key_returns_deterministic_fallback(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key=None),
            client=_FailingClient(),
        )

        self.assertEqual(run.question, CUSTOM_QUESTION)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_advisory_question_falls_back_before_openai_client(self) -> None:
        with patch(
            "app.agentic.pipeline.OpenAIResearchClient"
        ) as research_client:
            run = run_agentic_research_pipeline(
                ResearchRunRequest(question="Should I buy Nvidia?"),
                config=_config(enabled=True, api_key="test-openai-key"),
            )

        research_client.assert_not_called()
        self.assertEqual(run.question, "Should I buy Nvidia?")
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

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

    def test_malformed_agentic_output_falls_back(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_framework"] = {"not": "valid"}

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(responses),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_out_of_scope_planner_output_falls_back(self) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_planner"] = {
            **responses["agentic_planner"],
            "scope": "out_of_scope",
            "rejectedReason": "Requests a price target.",
        }

        run = run_agentic_research_pipeline(
            ResearchRunRequest(question="What is the price target for RY?"),
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

    def test_data_evidence_falls_back_when_web_search_is_disabled(self) -> None:
        run = run_agentic_research_pipeline(
            ResearchRunRequest(question=CUSTOM_QUESTION),
            config=_config(enabled=True, api_key="test-openai-key"),
            client=_FakeClient(_valid_stage_responses(_valid_agentic_run())),
        )

        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_data_evidence_falls_back_when_source_label_is_not_verified(
        self,
    ) -> None:
        responses = _valid_stage_responses(_valid_agentic_run())
        responses["agentic_source_research"]["sourceNotes"][0][
            "sourceLabel"
        ] = "Bureau of Labor Statistics"

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

    def create_structured_response(self, **kwargs: object) -> dict[str, object]:
        stage_name = str(kwargs["stage_name"])
        self.stage_names.append(stage_name)
        return self._responses[stage_name]


class _FailingClient:
    def create_structured_response(self, **_: object) -> dict[str, object]:
        raise AssertionError("OpenAI client should not be called")


def _config(
    *,
    enabled: bool,
    api_key: str | None,
    web_search_enabled: bool = False,
) -> AgenticResearchConfig:
    return AgenticResearchConfig(
        enabled=enabled,
        api_key=api_key,
        model="gpt-5.4-mini",
        web_search_enabled=web_search_enabled,
        timeout_seconds=1.0,
    )


def _valid_agentic_run(
    *,
    headline: str | None = None,
    thesis: str | None = None,
):
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
        deep=True,
        update={
            "question": CUSTOM_QUESTION,
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
            item.sourceLabel = "US Census Bureau"
            item.sourceType = "Official trade data"
            item.sourceQuality = "High"
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


if __name__ == "__main__":
    unittest.main()
