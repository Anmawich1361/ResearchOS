from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass(frozen=True)
class AgenticFallbackDiagnostics:
    lastFallbackReason: str | None = None
    lastFallbackStage: str | None = None
    lastRunAt: str | None = None
    lastSucceededAt: str | None = None
    lastErrorType: str | None = None


_diagnostics = AgenticFallbackDiagnostics()
_lock = Lock()


def mark_agentic_run_started() -> None:
    global _diagnostics
    with _lock:
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=_diagnostics.lastFallbackReason,
            lastFallbackStage=_diagnostics.lastFallbackStage,
            lastRunAt=_utc_now(),
            lastSucceededAt=_diagnostics.lastSucceededAt,
            lastErrorType=_diagnostics.lastErrorType,
        )


def record_agentic_fallback(
    *,
    reason: str,
    stage: str,
    error_type: str | None = None,
) -> None:
    global _diagnostics
    with _lock:
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=reason,
            lastFallbackStage=stage,
            lastRunAt=_diagnostics.lastRunAt,
            lastSucceededAt=_diagnostics.lastSucceededAt,
            lastErrorType=error_type,
        )


def record_agentic_success() -> None:
    global _diagnostics
    with _lock:
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=_diagnostics.lastFallbackReason,
            lastFallbackStage=_diagnostics.lastFallbackStage,
            lastRunAt=_diagnostics.lastRunAt,
            lastSucceededAt=_utc_now(),
            lastErrorType=_diagnostics.lastErrorType,
        )


def get_agentic_diagnostics() -> dict[str, str | None]:
    with _lock:
        return asdict(_diagnostics)


def reset_agentic_diagnostics() -> None:
    global _diagnostics
    with _lock:
        _diagnostics = AgenticFallbackDiagnostics()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
