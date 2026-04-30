import json
import unittest
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from unittest.mock import patch

from app.data_sources import bank_of_canada


class BankOfCanadaDataSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        bank_of_canada._reset_policy_rate_state_for_tests()

    def tearDown(self) -> None:
        bank_of_canada._reset_policy_rate_state_for_tests()

    def test_valet_payload_parses_to_policy_rate_chart(self) -> None:
        with patch.object(
            bank_of_canada,
            "urlopen",
            return_value=_FakeResponse(_valid_payload()),
        ) as urlopen:
            chart = bank_of_canada.fetch_policy_rate_chart()

        urlopen.assert_called_once()
        self.assertIsNotNone(chart)
        assert chart is not None
        self.assertEqual(chart.title, "Policy rate path")
        self.assertEqual(
            chart.subtitle,
            "Bank of Canada Valet API | target overnight rate",
        )
        self.assertEqual(chart.unit, "%")
        self.assertEqual(
            [(point.period, point.value) for point in chart.data],
            [("Apr 16", 3.0), ("Apr 17", 2.75)],
        )

    def test_malformed_payload_returns_none_and_records_fallback(self) -> None:
        payload = {"observations": [{"d": "2026-04-17"}]}

        with patch.object(
            bank_of_canada,
            "urlopen",
            return_value=_FakeResponse(payload),
        ):
            chart = bank_of_canada.fetch_policy_rate_chart()

        status = bank_of_canada.get_policy_rate_status()

        self.assertIsNone(chart)
        self.assertEqual(status["lastResult"], "fallback")
        self.assertIn("ValueError", str(status["lastError"]))
        self.assertTrue(status["inFailureCooldown"])

    def test_cache_hit_avoids_second_external_call(self) -> None:
        with patch.object(
            bank_of_canada,
            "urlopen",
            return_value=_FakeResponse(_valid_payload()),
        ) as urlopen:
            first_chart = bank_of_canada.fetch_policy_rate_chart()
            second_chart = bank_of_canada.fetch_policy_rate_chart()

        status = bank_of_canada.get_policy_rate_status()

        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(first_chart, second_chart)
        self.assertEqual(status["lastResult"], "cached")
        self.assertTrue(status["cached"])
        self.assertFalse(status["inFailureCooldown"])

    def test_failed_fetch_records_fallback_status(self) -> None:
        with patch.object(
            bank_of_canada,
            "urlopen",
            side_effect=URLError("TLS verification failed"),
        ) as urlopen:
            chart = bank_of_canada.fetch_policy_rate_chart()

        status = bank_of_canada.get_policy_rate_status()

        self.assertIsNone(chart)
        urlopen.assert_called_once()
        self.assertEqual(status["lastResult"], "fallback")
        self.assertIn("URLError", str(status["lastError"]))
        self.assertTrue(status["inFailureCooldown"])
        self.assertIsNotNone(status["nextRetryAt"])

    def test_failure_cooldown_avoids_repeated_external_calls(self) -> None:
        with patch.object(
            bank_of_canada,
            "urlopen",
            side_effect=URLError("temporary outage"),
        ) as urlopen:
            first_chart = bank_of_canada.fetch_policy_rate_chart()
            second_chart = bank_of_canada.fetch_policy_rate_chart()

        status = bank_of_canada.get_policy_rate_status()

        self.assertIsNone(first_chart)
        self.assertIsNone(second_chart)
        self.assertEqual(urlopen.call_count, 1)
        self.assertEqual(status["lastResult"], "cooldown")
        self.assertTrue(status["inFailureCooldown"])
        self.assertIsNotNone(status["nextRetryAt"])

    def test_successful_fetch_clears_last_error_and_cooldown(self) -> None:
        with patch.object(
            bank_of_canada,
            "urlopen",
            side_effect=URLError("temporary outage"),
        ):
            self.assertIsNone(bank_of_canada.fetch_policy_rate_chart())

        _expire_failure_cooldown()

        with patch.object(
            bank_of_canada,
            "urlopen",
            return_value=_FakeResponse(_valid_payload()),
        ):
            chart = bank_of_canada.fetch_policy_rate_chart()

        status = bank_of_canada.get_policy_rate_status()

        self.assertIsNotNone(chart)
        self.assertEqual(status["lastResult"], "live")
        self.assertIsNone(status["lastError"])
        self.assertFalse(status["inFailureCooldown"])
        self.assertTrue(status["cached"])
        self.assertIsNotNone(status["lastLiveFetchAt"])


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _valid_payload() -> dict[str, object]:
    return {
        "observations": [
            {"d": "2026-04-17", "V39079": {"v": "2.75"}},
            {"d": "2026-04-18", "V39079": {"v": "not-a-number"}},
            {"d": "2026-04-16", "V39079": {"v": "3.00"}},
            {"d": "2026-04-19"},
        ]
    }


def _expire_failure_cooldown() -> None:
    with bank_of_canada._cache_lock:
        bank_of_canada._last_failure_at = datetime.now(
            timezone.utc
        ) - timedelta(seconds=bank_of_canada.FAILURE_COOLDOWN_SECONDS + 1)
        bank_of_canada._last_failure_at_monotonic = (
            bank_of_canada.monotonic()
            - bank_of_canada.FAILURE_COOLDOWN_SECONDS
            - 1
        )


if __name__ == "__main__":
    unittest.main()
