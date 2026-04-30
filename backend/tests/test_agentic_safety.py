import unittest

from app.agentic.safety import (
    contains_forbidden_advisory_intent,
    contains_forbidden_research_intent,
    validate_agentic_research_run,
)
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRunRequest


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
                self.assertTrue(contains_forbidden_research_intent(prompt))

    def test_research_intent_helper_detects_price_target_prompts(
        self,
    ) -> None:
        prompts = [
            "What is the price target for RY?",
            "What's your target price on RY?",
            "Target price for Nvidia?",
            "Target price of Apple?",
            "What is your PT on Tesla?",
            "Give me a PT for Nvidia.",
            "Give me a price target for Nvidia.",
            "What should my target price be for Apple?",
            "What is fair upside/downside to my target price?",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(contains_forbidden_research_intent(prompt))

    def test_research_intent_helper_detects_portfolio_prompts(
        self,
    ) -> None:
        prompts = [
            "How much of my portfolio should I put in Nvidia?",
            "What portfolio allocation should I use for Canadian banks?",
            "How large should my position be in Tesla?",
            "Should I overweight or underweight RY in my portfolio?",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(contains_forbidden_research_intent(prompt))

    def test_research_intent_helper_allows_safe_disclaimers(self) -> None:
        disclaimers = [
            "This is not a buy/sell recommendation.",
            "No buy/sell recommendations are provided.",
            "No price targets are provided.",
            "Do not give me a price target.",
            "Explain why price targets can be unreliable.",
            "Analyze valuation sensitivity without giving a price target.",
            "Analyze how rate cuts affect Canadian banks without recommendations.",
        ]

        for disclaimer in disclaimers:
            with self.subTest(disclaimer=disclaimer):
                self.assertFalse(
                    contains_forbidden_research_intent(disclaimer)
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

        run = _without_data_evidence(run)

        result = validate_agentic_research_run(run)

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

        run = _without_data_evidence(run)

        result = validate_agentic_research_run(run)

        self.assertFalse(result.passed)
        self.assertIn(
            "forbidden recommendation or price-target language",
            result.reasons,
        )

    def test_forbidden_portfolio_allocation_language_fails(self) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(
            deep=True,
            update={
                "thesis": (
                    "Portfolio allocation should increase based on your "
                    "risk tolerance."
                )
            },
        )

        run = _without_data_evidence(run)

        result = validate_agentic_research_run(run)

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

        run = _without_data_evidence(run)

        result = validate_agentic_research_run(run)

        self.assertFalse(result.passed)
        self.assertIn("charts are empty", result.reasons)
        self.assertIn("evidence board is empty", result.reasons)

    def test_agentic_data_evidence_is_rejected(self) -> None:
        run = _run_with_data_source_label("US Census Bureau")

        result = validate_agentic_research_run(run)

        self.assertFalse(result.passed)
        self.assertIn(
            "agentic output cannot use Data evidence",
            result.reasons,
        )

    def test_agentic_output_without_data_evidence_can_pass(self) -> None:
        run = _run_without_data_evidence()

        result = validate_agentic_research_run(run)

        self.assertTrue(result.passed, result.reasons)

    def test_deterministic_research_run_can_still_use_data_evidence(
        self,
    ) -> None:
        run = run_research_pipeline(
            ResearchRunRequest(
                question="How would rate cuts affect Canadian banks?"
            )
        )

        self.assertTrue(any(item.type == "Data" for item in run.evidence))


def _without_data_evidence(run):
    for item in run.evidence:
        if item.type == "Data":
            item.type = "Source claim"
    for node in run.transmissionNodes:
        if node.evidenceType == "Data":
            node.evidenceType = "Source claim"
    return run


def _run_without_data_evidence():
    return _without_data_evidence(
        CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
    )


def _run_with_data_source_label(source_label: str):
    run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
    for item in run.evidence:
        if item.type == "Data":
            item.sourceLabel = source_label
            item.sourceType = "Official data"
            item.sourceQuality = "High"
    return run


if __name__ == "__main__":
    unittest.main()
