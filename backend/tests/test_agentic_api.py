import json
import os
import unittest
from unittest.mock import patch

from app.agentic.status import get_agentic_research_status
from app.main import (
    research_agentic_status,
    run_agentic_research,
    run_research,
)
from app.demo_cases import CANADIAN_BANKS_RESEARCH_RUN
from app.schemas import ResearchRunRequest


class AgenticApiTest(unittest.TestCase):
    def test_agentic_status_works_without_openai_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            status = get_agentic_research_status()

        self.assertEqual(status["mode"], "disabled")
        self.assertFalse(status["enabled"])
        self.assertFalse(status["configured"])

    def test_agentic_status_does_not_expose_secrets(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AGENTIC_RESEARCH_ENABLED": "true",
                "OPENAI_API_KEY": "test-secret-value",
            },
            clear=True,
        ):
            status = research_agentic_status()

        encoded = json.dumps(status, sort_keys=True)
        self.assertNotIn("test-secret-value", encoded)
        self.assertEqual(status["mode"], "configured")

    def test_agentic_run_falls_back_when_disabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            run = run_agentic_research(
                ResearchRunRequest(question="Unknown custom question")
            )

        self.assertEqual(run.question, "Unknown custom question")
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_agentic_run_falls_back_when_openai_key_is_missing(self) -> None:
        with patch.dict(
            os.environ,
            {"AGENTIC_RESEARCH_ENABLED": "true"},
            clear=True,
        ):
            run = run_agentic_research(
                ResearchRunRequest(question="Unknown custom question")
            )

        self.assertEqual(run.question, "Unknown custom question")
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)

    def test_existing_research_run_behavior_is_unchanged(self) -> None:
        run = run_research(
            ResearchRunRequest(
                question=(
                    "What happens to airlines if oil prices rise while "
                    "consumer demand weakens?"
                )
            )
        )

        self.assertEqual(run.scenario, "Oil shock plus weaker travel demand")

    def test_unknown_deterministic_fallback_remains_canadian_banks(self) -> None:
        run = run_research(
            ResearchRunRequest(question="Unknown custom question")
        )

        self.assertEqual(run.question, "Unknown custom question")
        self.assertEqual(run.scenario, CANADIAN_BANKS_RESEARCH_RUN.scenario)


if __name__ == "__main__":
    unittest.main()
