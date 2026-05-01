from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4


@dataclass(frozen=True)
class AgenticFallbackDiagnostics:
    lastFallbackReason: str | None = None
    lastFallbackStage: str | None = None
    lastRunAt: str | None = None
    lastSucceededAt: str | None = None
    lastErrorType: str | None = None


_diagnostics = AgenticFallbackDiagnostics()
_active_run_id: str | None = None
_closed_run_ids: set[str] = set()
_lock = Lock()


def mark_agentic_run_started() -> str:
    global _active_run_id, _closed_run_ids, _diagnostics
    run_id = uuid4().hex
    with _lock:
        _active_run_id = run_id
        _closed_run_ids = set()
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=_diagnostics.lastFallbackReason,
            lastFallbackStage=_diagnostics.lastFallbackStage,
            lastRunAt=_utc_now(),
            lastSucceededAt=_diagnostics.lastSucceededAt,
            lastErrorType=_diagnostics.lastErrorType,
        )
    return run_id


def close_agentic_run(run_id: str) -> None:
    with _lock:
        if run_id == _active_run_id:
            _closed_run_ids.add(run_id)


def record_agentic_fallback(
    *,
    run_id: str,
    reason: str,
    stage: str,
    error_type: str | None = None,
) -> bool:
    global _diagnostics
    with _lock:
        if not _run_can_write(run_id):
            return False
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=reason,
            lastFallbackStage=stage,
            lastRunAt=_diagnostics.lastRunAt,
            lastSucceededAt=_diagnostics.lastSucceededAt,
            lastErrorType=error_type,
        )
    return True


def record_agentic_success(*, run_id: str) -> bool:
    global _diagnostics
    with _lock:
        if not _run_can_write(run_id):
            return False
        _diagnostics = AgenticFallbackDiagnostics(
            lastFallbackReason=_diagnostics.lastFallbackReason,
            lastFallbackStage=_diagnostics.lastFallbackStage,
            lastRunAt=_diagnostics.lastRunAt,
            lastSucceededAt=_utc_now(),
            lastErrorType=_diagnostics.lastErrorType,
        )
    return True


def get_agentic_diagnostics() -> dict[str, str | None]:
    with _lock:
        return asdict(_diagnostics)


def reset_agentic_diagnostics() -> None:
    global _active_run_id, _closed_run_ids, _diagnostics
    with _lock:
        _active_run_id = None
        _closed_run_ids = set()
        _diagnostics = AgenticFallbackDiagnostics()


def _run_can_write(run_id: str) -> bool:
    return run_id == _active_run_id and run_id not in _closed_run_ids


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
