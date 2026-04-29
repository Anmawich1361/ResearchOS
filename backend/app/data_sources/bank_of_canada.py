import json
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.schemas import ChartPoint, ChartSeries

POLICY_RATE_SERIES = "V39079"
POLICY_RATE_URL = (
    "https://www.bankofcanada.ca/valet/observations/"
    f"{POLICY_RATE_SERIES}/json?recent=8"
)
REQUEST_TIMEOUT_SECONDS = 3


def fetch_policy_rate_chart() -> ChartSeries | None:
    request = Request(
        POLICY_RATE_URL,
        headers={"User-Agent": "ResearchOS Bank of Canada data client"},
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    return _policy_rate_chart_from_payload(payload)


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
