import json
import logging
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.schemas import ChartPoint, ChartSeries

POLICY_RATE_SERIES = "V39079"
POLICY_RATE_URL = (
    "https://www.bankofcanada.ca/valet/observations/"
    f"{POLICY_RATE_SERIES}/json?recent=8"
)
REQUEST_TIMEOUT_SECONDS = 3
CACHE_TTL_SECONDS = 30 * 60
FAILURE_COOLDOWN_SECONDS = 5 * 60

_logger = logging.getLogger(__name__)

_cache_lock = Lock()
_cached_chart: ChartSeries | None = None
_cached_at_monotonic: float | None = None
_last_attempt_at: datetime | None = None
_last_live_fetch_at: datetime | None = None
_last_failure_at: datetime | None = None
_last_failure_at_monotonic: float | None = None
_last_result = "not_requested"
_last_error: str | None = None


def fetch_policy_rate_chart() -> ChartSeries | None:
    cached_chart = _get_cached_chart()
    if cached_chart is not None:
        _record_cache_hit()
        _logger.info("Using cached Bank of Canada policy-rate chart")
        return cached_chart

    if _is_failure_cooldown_active():
        _record_failure_cooldown_skip()
        _logger.info("Skipping Bank of Canada fetch during failure cooldown")
        return None

    _record_attempt()
    request = Request(
        POLICY_RATE_URL,
        headers={"User-Agent": "ResearchOS Bank of Canada data client"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        _record_failure(exc)
        _logger.warning(
            "Bank of Canada fetch failed; using deterministic fallback: %s",
            _safe_error(exc),
        )
        return None

    chart = _policy_rate_chart_from_payload(payload)
    if chart is None:
        _record_failure(
            ValueError(
                "Bank of Canada response did not contain enough "
                "policy-rate points"
            )
        )
        _logger.warning(
            "Bank of Canada payload was invalid; using deterministic fallback"
        )
        return None

    _record_success(chart)
    _logger.info("Fetched Bank of Canada policy-rate chart")
    return chart


def get_policy_rate_status() -> dict[str, object]:
    with _cache_lock:
        now = monotonic()
        cached = _is_cache_fresh(now)
        in_failure_cooldown = _is_failure_cooldown_active_at(now)
        return {
            "source": "Bank of Canada Valet API",
            "series": POLICY_RATE_SERIES,
            "url": POLICY_RATE_URL,
            "cacheTtlSeconds": CACHE_TTL_SECONDS,
            "failureCooldownSeconds": FAILURE_COOLDOWN_SECONDS,
            "cached": cached,
            "inFailureCooldown": in_failure_cooldown,
            "nextRetryAt": _next_retry_at(in_failure_cooldown),
            "lastResult": _last_result,
            "lastAttemptAt": _isoformat(_last_attempt_at),
            "lastLiveFetchAt": _isoformat(_last_live_fetch_at),
            "lastError": _last_error,
        }


def _policy_rate_chart_from_payload(payload: object) -> ChartSeries | None:
    if not isinstance(payload, dict):
        return None

    observations = payload.get("observations")
    if not isinstance(observations, list):
        return None

    points: list[tuple[datetime, ChartPoint]] = []
    for observation in observations:
        point = _point_from_observation(observation)
        if point:
            points.append(point)

    if len(points) < 2:
        return None

    ordered_points = [
        point for _, point in sorted(points, key=lambda item: item[0])
    ]
    return ChartSeries(
        title="Policy rate path",
        subtitle="Bank of Canada Valet API | target overnight rate",
        unit="%",
        tone="cyan",
        data=ordered_points,
    )


def _point_from_observation(observation: object) -> tuple[datetime, ChartPoint] | None:
    if not isinstance(observation, dict):
        return None

    date_raw = observation.get("d")
    series_value = observation.get(POLICY_RATE_SERIES)
    if not isinstance(date_raw, str) or not isinstance(series_value, dict):
        return None

    value_raw = series_value.get("v")
    if not isinstance(value_raw, str):
        return None

    try:
        date_value = datetime.strptime(date_raw, "%Y-%m-%d")
        value = float(value_raw)
    except ValueError:
        return None

    label = f"{date_value:%b} {date_value.day}"
    return date_value, ChartPoint(period=label, value=value)


def _get_cached_chart() -> ChartSeries | None:
    with _cache_lock:
        if not _is_cache_fresh(monotonic()):
            return None

        return _cached_chart


def _record_attempt() -> None:
    global _last_attempt_at

    with _cache_lock:
        _last_attempt_at = datetime.now(timezone.utc)


def _record_success(chart: ChartSeries) -> None:
    global _cached_at_monotonic
    global _cached_chart
    global _last_error
    global _last_failure_at
    global _last_failure_at_monotonic
    global _last_live_fetch_at
    global _last_result

    with _cache_lock:
        _cached_chart = chart
        _cached_at_monotonic = monotonic()
        _last_live_fetch_at = datetime.now(timezone.utc)
        _last_result = "live"
        _last_error = None
        _last_failure_at = None
        _last_failure_at_monotonic = None


def _record_cache_hit() -> None:
    global _last_error
    global _last_failure_at
    global _last_failure_at_monotonic
    global _last_result

    with _cache_lock:
        _last_result = "cached"
        _last_error = None
        _last_failure_at = None
        _last_failure_at_monotonic = None


def _record_failure(exc: Exception) -> None:
    global _last_error
    global _last_failure_at
    global _last_failure_at_monotonic
    global _last_result

    with _cache_lock:
        _last_failure_at = datetime.now(timezone.utc)
        _last_failure_at_monotonic = monotonic()
        _last_result = "fallback"
        _last_error = _safe_error(exc)


def _record_failure_cooldown_skip() -> None:
    global _last_result

    with _cache_lock:
        _last_result = "cooldown"


def _is_cache_fresh(now: float) -> bool:
    if _cached_chart is None or _cached_at_monotonic is None:
        return False

    return now - _cached_at_monotonic < CACHE_TTL_SECONDS


def _is_failure_cooldown_active() -> bool:
    with _cache_lock:
        return _is_failure_cooldown_active_at(monotonic())


def _is_failure_cooldown_active_at(now: float) -> bool:
    if _last_failure_at_monotonic is None:
        return False

    return now - _last_failure_at_monotonic < FAILURE_COOLDOWN_SECONDS


def _next_retry_at(in_failure_cooldown: bool) -> str | None:
    if not in_failure_cooldown or _last_failure_at is None:
        return None

    return _isoformat(
        _last_failure_at + timedelta(seconds=FAILURE_COOLDOWN_SECONDS)
    )


def _isoformat(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def _safe_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def _reset_policy_rate_state_for_tests() -> None:
    global _cached_at_monotonic
    global _cached_chart
    global _last_attempt_at
    global _last_error
    global _last_failure_at
    global _last_failure_at_monotonic
    global _last_live_fetch_at
    global _last_result

    with _cache_lock:
        _cached_chart = None
        _cached_at_monotonic = None
        _last_attempt_at = None
        _last_live_fetch_at = None
        _last_failure_at = None
        _last_failure_at_monotonic = None
        _last_result = "not_requested"
        _last_error = None
