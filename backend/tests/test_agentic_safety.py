import unittest

from app.agentic.safety import validate_agentic_research_run
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN


class AgenticSafetyTest(unittest.TestCase):
    def test_safe_disclaimer_does_not_trigger_recommendation_failure(
        self,
    ) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
        run.memo[0].title = "Boundary"
        run.memo[0].body = (
            "This is not a buy/sell recommendation. The research remains a "
            "macro-transmission scenario."
        )

        result = validate_agentic_research_run(run, source_backed=False)

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

        result = validate_agentic_research_run(run, source_backed=False)

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

        result = validate_agentic_research_run(run, source_backed=False)

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

        result = validate_agentic_research_run(run, source_backed=False)

        self.assertFalse(result.passed)
        self.assertIn("charts are empty", result.reasons)
        self.assertIn("evidence board is empty", result.reasons)

    def test_source_backed_data_claim_requires_specific_source_label(
        self,
    ) -> None:
        run = CANADIAN_BANKS_RESEARCH_RUN.model_copy(deep=True)
        run.evidence[0].sourceLabel = "Source"

        result = validate_agentic_research_run(run, source_backed=True)

        self.assertFalse(result.passed)
        self.assertIn(
            "source-backed Data claim has weak source label",
            result.reasons,
        )


if __name__ == "__main__":
    unittest.main()
