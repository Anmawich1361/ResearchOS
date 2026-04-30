import unittest
from unittest.mock import patch

from app.demo_cases import (
    AI_CAPEX_SEMIS_RESEARCH_RUN,
    CANADIAN_BANKS_RESEARCH_RUN,
    OIL_AIRLINES_RESEARCH_RUN,
)
from app.orchestrator import run_research_pipeline
from app.schemas import ChartPoint, ChartSeries, EvidenceItem, ResearchRunRequest


BOC_SOURCE_LABEL = "Bank of Canada Valet API"


class ResearchOrchestratorTest(unittest.TestCase):
    def test_explicit_canadian_banks_question_applies_boc_chart(self) -> None:
        with patch(
            "app.orchestrator.fetch_policy_rate_chart",
            return_value=_live_policy_rate_chart(),
        ) as fetch_policy_rate_chart:
            run = run_research_pipeline(
                ResearchRunRequest(
                    question="How would rate cuts affect Canadian banks?"
                )
            )

        fetch_policy_rate_chart.assert_called_once_with()
        policy_rate_chart = _policy_rate_chart(run.charts)

        self.assertEqual(
            policy_rate_chart.subtitle,
            "Bank of Canada Valet API | target overnight rate",
        )
        self.assertTrue(_has_boc_evidence(run.evidence))

    def test_unknown_question_falls_back_without_boc_fetch(self) -> None:
        with patch(
            "app.orchestrator.fetch_policy_rate_chart",
            side_effect=AssertionError("BoC fetch should not be called"),
        ) as fetch_policy_rate_chart:
            run = run_research_pipeline(
                ResearchRunRequest(question="Unknown custom question")
            )

        fetch_policy_rate_chart.assert_not_called()
        self.assertEqual(run.question, "Unknown custom question")
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)
        self.assertEqual(run.charts, CANADIAN_BANKS_RESEARCH_RUN.charts)
        self.assertFalse(_has_boc_evidence(run.evidence))

    def test_oil_airlines_question_does_not_call_boc_fetch(self) -> None:
        with patch(
            "app.orchestrator.fetch_policy_rate_chart",
            side_effect=AssertionError("BoC fetch should not be called"),
        ) as fetch_policy_rate_chart:
            run = run_research_pipeline(
                ResearchRunRequest(
                    question=(
                        "What happens to airlines if oil prices rise while "
                        "consumer demand weakens?"
                    )
                )
            )

        fetch_policy_rate_chart.assert_not_called()
        self.assertEqual(run.scenario, OIL_AIRLINES_RESEARCH_RUN.scenario)
        self.assertEqual(run.charts, OIL_AIRLINES_RESEARCH_RUN.charts)
        self.assertEqual(run.evidence, OIL_AIRLINES_RESEARCH_RUN.evidence)

    def test_ai_capex_question_does_not_call_boc_fetch(self) -> None:
        with patch(
            "app.orchestrator.fetch_policy_rate_chart",
            side_effect=AssertionError("BoC fetch should not be called"),
        ) as fetch_policy_rate_chart:
            run = run_research_pipeline(
                ResearchRunRequest(
                    question=(
                        "Is AI capex becoming a risk for semiconductors and "
                        "hyperscalers?"
                    )
                )
            )

        fetch_policy_rate_chart.assert_not_called()
        self.assertEqual(run.scenario, AI_CAPEX_SEMIS_RESEARCH_RUN.scenario)
        self.assertEqual(run.charts, AI_CAPEX_SEMIS_RESEARCH_RUN.charts)
        self.assertEqual(run.evidence, AI_CAPEX_SEMIS_RESEARCH_RUN.evidence)

    def test_explicit_canadian_banks_question_preserves_fallback_on_boc_failure(
        self,
    ) -> None:
        with patch(
            "app.orchestrator.fetch_policy_rate_chart",
            return_value=None,
        ) as fetch_policy_rate_chart:
            run = run_research_pipeline(
                ResearchRunRequest(
                    question="How would rate cuts affect Canadian banks?"
                )
            )

        fetch_policy_rate_chart.assert_called_once_with()
        self.assertEqual(run.charts, CANADIAN_BANKS_RESEARCH_RUN.charts)
        self.assertFalse(_has_boc_evidence(run.evidence))


def _live_policy_rate_chart() -> ChartSeries:
    return ChartSeries(
        title="Policy rate path",
        subtitle="Bank of Canada Valet API | target overnight rate",
        unit="%",
        tone="cyan",
        data=[
            ChartPoint(period="Apr 22", value=2.75),
            ChartPoint(period="Apr 23", value=2.5),
        ],
    )


def _policy_rate_chart(charts: list[ChartSeries]) -> ChartSeries:
    return next(chart for chart in charts if chart.title == "Policy rate path")


def _has_boc_evidence(evidence: list[EvidenceItem]) -> bool:
    return any(item.sourceLabel == BOC_SOURCE_LABEL for item in evidence)


if __name__ == "__main__":
    unittest.main()
