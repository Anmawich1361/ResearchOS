import unittest
from unittest.mock import patch

from app.demo_cases import (
    AI_CAPEX_SEMIS_RESEARCH_RUN,
    CANADIAN_BANKS_RESEARCH_RUN,
    OIL_AIRLINES_RESEARCH_RUN,
)
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRun, ResearchRunRequest


ALLOWED_EVIDENCE_LABELS = {
    "Data",
    "Source claim",
    "Framework inference",
    "Narrative signal",
    "Open question",
}
BOC_SOURCE_LABEL = "Bank of Canada Valet API"
GOLDEN_PATH_QUESTIONS = [
    "How would rate cuts affect Canadian banks?",
    "What happens to airlines if oil prices rise while consumer demand weakens?",
    "Is AI capex becoming a risk for semiconductors and hyperscalers?",
]


class ResearchRunContractTest(unittest.TestCase):
    def test_golden_path_questions_return_required_sections(self) -> None:
        for question in GOLDEN_PATH_QUESTIONS:
            with self.subTest(question=question):
                run = _run_with_boc_fallback(question)

                self.assertEqual(run.question, question)
                self.assertTrue(run.transmissionNodes)
                self.assertTrue(run.transmissionEdges)
                self.assertTrue(run.charts)
                self.assertTrue(run.evidence)
                self.assertTrue(run.memo)
                self.assertTrue(run.openQuestions)

    def test_unknown_question_returns_deterministic_canadian_banks_fallback(
        self,
    ) -> None:
        question = "Unknown custom question"
        run = _run_asserting_no_boc_fetch(question)

        self.assertEqual(run.question, question)
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        self.assertTrue(run.charts)
        self.assertTrue(run.evidence)
        self.assertTrue(run.transmissionNodes)
        self.assertFalse(_has_boc_evidence(run))

    def test_evidence_labels_are_restricted_to_contract_taxonomy(self) -> None:
        questions = [
            *GOLDEN_PATH_QUESTIONS,
            "Unknown custom question",
        ]

        for question in questions:
            with self.subTest(question=question):
                run = _run_with_boc_fallback(question)
                evidence_types = {item.type for item in run.evidence}
                node_evidence_types = {
                    node.evidenceType
                    for node in run.transmissionNodes
                }

                self.assertLessEqual(
                    evidence_types,
                    ALLOWED_EVIDENCE_LABELS,
                )
                self.assertLessEqual(
                    node_evidence_types,
                    ALLOWED_EVIDENCE_LABELS,
                )

    def test_non_boc_cases_do_not_include_boc_evidence(self) -> None:
        cases = [
            (
                "What happens to airlines if oil prices rise while consumer "
                "demand weakens?",
                OIL_AIRLINES_RESEARCH_RUN.scenario,
            ),
            (
                "Is AI capex becoming a risk for semiconductors and "
                "hyperscalers?",
                AI_CAPEX_SEMIS_RESEARCH_RUN.scenario,
            ),
            (
                "Unknown custom question",
                CANADIAN_BANKS_RESEARCH_RUN.scenario,
            ),
        ]

        for question, expected_scenario in cases:
            with self.subTest(question=question):
                run = _run_asserting_no_boc_fetch(question)

                self.assertEqual(run.scenario, expected_scenario)
                self.assertFalse(_has_boc_evidence(run))

    def test_mixed_prompts_route_without_boc_evidence(self) -> None:
        cases = [
            (
                "What happens to airlines if oil prices rise while Canadian "
                "banks face rate cuts?",
                OIL_AIRLINES_RESEARCH_RUN.scenario,
            ),
            (
                "Is AI capex becoming a risk for semiconductors while "
                "Canadian banks face BoC cuts?",
                AI_CAPEX_SEMIS_RESEARCH_RUN.scenario,
            ),
        ]

        for question, expected_scenario in cases:
            with self.subTest(question=question):
                run = _run_asserting_no_boc_fetch(question)

                self.assertEqual(run.scenario, expected_scenario)
                self.assertFalse(_has_boc_evidence(run))


def _run_with_boc_fallback(question: str) -> ResearchRun:
    with patch("app.orchestrator.fetch_policy_rate_chart", return_value=None):
        return run_research_pipeline(ResearchRunRequest(question=question))


def _run_asserting_no_boc_fetch(question: str) -> ResearchRun:
    with patch(
        "app.orchestrator.fetch_policy_rate_chart",
        side_effect=AssertionError("BoC fetch should not be called"),
    ) as fetch_policy_rate_chart:
        run = run_research_pipeline(ResearchRunRequest(question=question))

    fetch_policy_rate_chart.assert_not_called()
    return run


def _has_boc_evidence(run: ResearchRun) -> bool:
    return any(
        item.sourceLabel == BOC_SOURCE_LABEL
        for item in run.evidence
    )


if __name__ == "__main__":
    unittest.main()
