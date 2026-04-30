import unittest

from app.agentic.safety import (
    contains_forbidden_advisory_intent,
    validate_agentic_research_run,
)
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN


class AgenticSafetyTest(unittest.TestCase):
    def test_advisory_intent_helper_detects_direct_prompts(self) -> None:
        prompts = [
            "Should I buy Nvidia?",
            "Should we sell Canadian banks?",
            "Should I hold Apple?",
            "Should I short Tesla?",
            "Should I accumulate Microsoft?",
            "Should investors buy Nvidia?",
            "Would you buy the stock?",
            "Would you sell the stock?",
            "Do you recommend buying the shares?",
            "Do you recommend selling the shares?",
            "Is Nvidia a buy?",
            "Is Nvidia a sell?",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(contains_forbidden_advisory_intent(prompt))

    def test_advisory_intent_helper_allows_safe_disclaimers(self) -> None:
        disclaimers = [
            "This is not a buy/sell recommendation.",
            "No buy/sell recommendations are provided.",
        ]

        for disclaimer in disclaimers:
            with self.subTest(disclaimer=disclaimer):
                self.assertFalse(
                    contains_forbidden_advisory_intent(disclaimer)
                )

    def test_safe_disclaimer_does_not_trigger_recommendation_failure(
        self,
    ) -> None:
        run = _run_without_data_evidence()
        run.memo[0].title = "Boundary"
        run.memo[0].body = (
            "This is not a buy/sell recommendation. The research remains a "
            "macro-transmission scenario."
        )

        result = validate_agentic_research_run(run)

        self.assertTrue(result.passed, result.reasons)

    def test_forbidden_price_target_language_fails(self) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
            deep=True,
            update={
                "thesis": (
                    "The analysis includes a price target for the sector."
                )
            },
        )

        result = validate_agentic_research_run(
            run,
            verified_source_labels=_data_source_labels(run),
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "forbidden recommendation or price-target language",
            result.reasons,
        )

    def test_forbidden_buy_recommendation_language_fails(self) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
            deep=True,
            update={"headline": "Investors should buy the stock now."},
        )

        result = validate_agentic_research_run(
            run,
            verified_source_labels=_data_source_labels(run),
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "forbidden recommendation or price-target language",
            result.reasons,
        )

    def test_empty_required_sections_fail(self) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
            deep=True,
            update={"charts": [], "evidence": []},
        )

        result = validate_agentic_research_run(
            run,
            verified_source_labels=_data_source_labels(run),
        )

        self.assertFalse(result.passed)
        self.assertIn("charts are empty", result.reasons)
        self.assertIn("evidence board is empty", result.reasons)

    def test_data_claim_fails_without_verified_source_labels(self) -> None:
        run = _run_with_data_source_label("US Census Bureau")

        result = validate_agentic_research_run(run)

        self.assertFalse(result.passed)
        self.assertIn(
            "Data evidence requires verified source research",
            result.reasons,
        )

    def test_data_claim_requires_specific_source_label(self) -> None:
        run = _run_with_data_source_label("Source")

        result = validate_agentic_research_run(
            run,
            verified_source_labels={"Source"},
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "Data evidence has weak source label",
            result.reasons,
        )

    def test_data_claim_requires_matching_verified_source_label(self) -> None:
        run = _run_with_data_source_label("US Census Bureau")

        result = validate_agentic_research_run(
            run,
            verified_source_labels={"Bureau of Labor Statistics"},
        )

        self.assertFalse(result.passed)
        self.assertIn(
            "Data evidence source label is not verified",
            result.reasons,
        )

    def test_data_claim_passes_with_matching_verified_source_label(self) -> None:
        run = _run_with_data_source_label("US Census Bureau")

        result = validate_agentic_research_run(
            run,
            verified_source_labels={"US Census Bureau"},
        )

        self.assertTrue(result.passed, result.reasons)


def _run_without_data_evidence():
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
    for item in run.evidence:
        if item.type == "Data":
            item.type = "Source claim"
    for node in run.transmissionNodes:
        if node.evidenceType == "Data":
            node.evidenceType = "Source claim"
    return run


def _run_with_data_source_label(source_label: str):
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
    for item in run.evidence:
        if item.type == "Data":
            item.sourceLabel = source_label
            item.sourceType = "Official data"
            item.sourceQuality = "High"
    return run


def _data_source_labels(run) -> set[str]:
    return {
        item.sourceLabel
        for item in run.evidence
        if item.type == "Data" and item.sourceLabel
    }


if __name__ == "__main__":
    unittest.main()
