import unittest
from unittest.mock import patch

from app.agentic.config import AgenticResearchConfig
from app.agentic.evals import (
    ALL_AGENTIC_EVAL_CASES,
    BLOCKED_PROMPT_CASES,
    DATA_EVIDENCE_MISUSE_CASE,
    OUTPUT_CONTRACT_CASE,
    SOURCE_FABRICATION_CASE,
    VALID_MACRO_TRANSMISSION_CASES,
)
from app.agentic.pipeline import run_agentic_research_pipeline
from app.agentic.safety import contains_forbidden_research_intent
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRun, ResearchRunRequest


ALLOWED_EVIDENCE_LABELS = {
    "Data",
    "Source claim",
    "Framework inference",
    "Narrative signal",
    "Open question",
}


class AgenticEvalHarnessTest(unittest.TestCase):
    def test_eval_cases_have_required_metadata(self) -> None:
        names = set()

        for case in ALL_AGENTIC_EVAL_CASES:
            with self.subTest(case=case.name):
                self.assertTrue(case.name)
                self.assertNotIn(case.name, names)
                names.add(case.name)
                self.assertTrue(case.prompt)
                self.assertTrue(case.category)
                self.assertTrue(case.expected_behavior)
                self.assertIsInstance(case.should_call_openai, bool)
                self.assertIsInstance(case.fallback_expected, bool)
                self.assertTrue(case.forbidden_output_markers)

    def test_blocked_prompts_fallback_before_openai_client(self) -> None:
        for case in BLOCKED_PROMPT_CASES:
            with self.subTest(case=case.name):
                with patch(
                    "app.agentic.pipeline.OpenAIResearchClient"
                ) as research_client:
                    run = _run_agentic(case.prompt)

                self.assertFalse(case.should_call_openai)
                self.assertTrue(case.fallback_expected)
                research_client.assert_not_called()
                self.assertEqual(run.question, case.prompt)
                self.assertEqual(
                    run.scenario,
                    CANADIAN_BANKS_RESEARCH_RUN.scenario,
                )

    def test_non_personal_allocation_prompts_are_not_preflight_blocked(
        self,
    ) -> None:
        prompts = [
            "What allocation should I use across business drivers?",
            "How should allocation shift across capex buckets?",
            "How should management allocate capital between buybacks and R&D?",
            "What capital allocation choices matter for semiconductors?",
            "How should research time be allocated across valuation drivers?",
            "Analyze capital allocation tradeoffs without portfolio advice.",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertFalse(contains_forbidden_research_intent(prompt))

    def test_valid_macro_prompts_enter_mocked_agentic_path(self) -> None:
        for case in VALID_MACRO_TRANSMISSION_CASES:
            with self.subTest(case=case.name):
                client = _FakeClient(
                    _stage_responses(_agentic_run_for_prompt(case.prompt))
                )

                run = _run_agentic(case.prompt, client=client)

                self.assertTrue(case.should_call_openai)
                self.assertFalse(case.fallback_expected)
                self.assertEqual(run.question, case.prompt)
                self.assertEqual(
                    run.scenario,
                    "Agentic eval macro transmission",
                )
                self.assertEqual(client.stage_names, _EXPECTED_STAGE_NAMES)

    def test_data_evidence_misuse_falls_back(self) -> None:
        case = DATA_EVIDENCE_MISUSE_CASE
        client = _FakeClient(
            _stage_responses(
                _agentic_run_for_prompt(
                    case.prompt,
                    include_data_evidence=True,
                )
            )
        )

        run = _run_agentic(case.prompt, client=client)

        self.assertTrue(case.should_call_openai)
        self.assertTrue(case.fallback_expected)
        self.assertEqual(client.stage_names, _EXPECTED_STAGE_NAMES)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_source_note_spoofing_cannot_authorize_data_evidence(self) -> None:
        case = SOURCE_FABRICATION_CASE
        fake_source = "Fake Official Source"
        client = _FakeClient(
            _stage_responses(
                _agentic_run_for_prompt(
                    case.prompt,
                    include_data_evidence=True,
                    data_source_label=fake_source,
                ),
                source_label=fake_source,
            )
        )

        run = _run_agentic(case.prompt, client=client)

        self.assertTrue(case.should_call_openai)
        self.assertTrue(case.fallback_expected)
        self.assertEqual(client.stage_names, _EXPECTED_STAGE_NAMES)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_accepted_agentic_output_preserves_contract(self) -> None:
        case = OUTPUT_CONTRACT_CASE
        client = _FakeClient(
            _stage_responses(_agentic_run_for_prompt(case.prompt))
        )

        run = _run_agentic(case.prompt, client=client)

        self.assertIsInstance(run, ResearchRun)
        self.assertEqual(run.question, case.prompt)
        self.assertEqual(run.scenario, "Agentic eval macro transmission")
        self.assertTrue(run.transmissionNodes)
        self.assertTrue(run.transmissionEdges)
        self.assertTrue(run.charts)
        self.assertTrue(run.evidence)
        self.assertTrue(run.memo)
        self.assertTrue(run.openQuestions)
        self.assertLessEqual(
            {item.type for item in run.evidence},
            ALLOWED_EVIDENCE_LABELS,
        )
        self.assertLessEqual(
            {node.evidenceType for node in run.transmissionNodes},
            ALLOWED_EVIDENCE_LABELS,
        )

        encoded = run.model_dump_json().lower()
        for marker in case.forbidden_output_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), encoded)

    def test_deterministic_research_run_still_allows_data_evidence(self) -> None:
        run = run_research_pipeline(
            ResearchRunRequest(
                question="How would rate cuts affect Canadian banks?"
            )
        )

        self.assertTrue(any(item.type == "Data" for item in run.evidence))


_EXPECTED_STAGE_NAMES = [
    "agentic_planner",
    "agentic_source_research",
    "agentic_framework",
    "agentic_skeptic",
    "agentic_synthesis",
]


class _FakeClient:
    def __init__(self, responses: dict[str, dict[str, object]]) -> None:
        self._responses = responses
        self.stage_names: list[str] = []

    def create_structured_response(self, **kwargs: object) -> dict[str, object]:
        stage_name = str(kwargs["stage_name"])
        self.stage_names.append(stage_name)
        return self._responses[stage_name]


def _run_agentic(prompt: str, *, client: _FakeClient | None = None) -> ResearchRun:
    return run_agentic_research_pipeline(
        ResearchRunRequest(question=prompt),
        config=AgenticResearchConfig(
            enabled=True,
            api_key="test-openai-key",
            model="gpt-5.4-mini",
            web_search_enabled=False,
            timeout_seconds=1.0,
        ),
        client=client,
    )


def _agentic_run_for_prompt(
    prompt: str,
    *,
    include_data_evidence: bool = False,
    data_source_label: str = "Example Source Pack",
) -> ResearchRun:
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
        deep=True,
        update={
            "question": prompt,
            "timestamp": "Agentic eval run | mocked",
            "scenario": "Agentic eval macro transmission",
            "headline": (
                "The shock transmits through revenue translation, demand "
                "elasticity, margins, and balance-sheet assumptions."
            ),
            "thesis": (
                "The research case is conditional and depends on transmission "
                "channels, operating leverage, and company exposure."
            ),
        },
    )
    for item in run.evidence:
        if item.type == "Data":
            item.sourceLabel = data_source_label
            item.sourceType = "Model-authored source note"
            item.sourceQuality = "Medium"
            if not include_data_evidence:
                item.type = "Source claim"
    if not include_data_evidence:
        for node in run.transmissionNodes:
            if node.evidenceType == "Data":
                node.evidenceType = "Source claim"
    for agent in run.agents:
        agent.output = [
            "Mocked eval stage completed with structured research artifacts."
        ]
    run.memo[0].body = (
        "The mocked research run maps the macro shock into fundamentals, "
        "valuation drivers, and open questions."
    )
    run.memo[1].body = (
        "The decisive branch is whether the macro driver changes revenue, "
        "margin, or credit assumptions first."
    )
    run.memo[2].body = (
        "This mocked eval labels claims by evidence type and avoids "
        "unsupported company-specific conclusions."
    )
    return run


def _stage_responses(
    run: ResearchRun,
    *,
    source_label: str = "Example Source Pack",
) -> dict[str, dict[str, object]]:
    return {
        "agentic_planner": {
            "researchType": "macro_to_sector_shock",
            "shock": "macro shock",
            "affectedEntities": ["sector universe"],
            "drivers": [
                "Revenue sensitivity",
                "Margin pressure",
                "Balance-sheet transmission",
            ],
            "scope": "in_scope",
            "researchObjective": "Map the shock into fundamentals.",
            "rejectedReason": None,
        },
        "agentic_source_research": {
            "sourceNotes": [
                {
                    "sourceLabel": source_label,
                    "sourceType": "Model-authored source note",
                    "sourceQuality": "Medium",
                    "claim": "Source notes are compact and non-authorizing.",
                    "relevance": "Used only as mocked source context.",
                    "openQuestions": ["Which exposure metric matters most?"],
                }
            ],
            "openQuestions": ["Which exposure metric matters most?"],
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
