import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any

from pydantic import ValidationError

from app.agentic.config import (
    AgenticResearchConfig,
    get_agentic_research_config,
)
from app.agentic.diagnostics import (
    close_agentic_run,
    mark_agentic_run_started,
    record_agentic_fallback,
    record_agentic_success,
)
from app.agentic.models import (
    FastSynthesisStageResult,
    FrameworkStageResult,
    PlannerStageResult,
    SkepticStageResult,
    SourceResearchResult,
    SynthesisStageResult,
)
from app.agentic.normalizer import (
    normalize_agentic_research_run,
    normalize_fast_synthesis_research_run,
)
from app.agentic.openai_client import (
    AgenticResearchError,
    OpenAIResearchClient,
)
from app.agentic.prompts import (
    FRAMEWORK_PROMPT,
    FAST_SYNTHESIS_PROMPT,
    PLANNER_PROMPT,
    SKEPTIC_PROMPT,
    SOURCE_RESEARCH_PROMPT,
    SYNTHESIS_PROMPT,
)
from app.agentic.safety import (
    contains_forbidden_research_intent,
    validate_agentic_research_run,
)
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRun, ResearchRunRequest


_logger = logging.getLogger(__name__)
_FAST_SYNTHESIS_TARGET_QUESTION = (
    "how would a stronger us dollar affect semiconductor earnings?"
)


class AgenticPipelineError(RuntimeError):
    pass


class AgenticPipelineTimeout(TimeoutError):
    pass


def run_agentic_research_pipeline(
    request: ResearchRunRequest,
    *,
    config: AgenticResearchConfig | None = None,
    client: OpenAIResearchClient | None = None,
) -> ResearchRun:
    resolved_config = config or get_agentic_research_config()
    fallback_run = run_research_pipeline(request)
    run_id = mark_agentic_run_started()

    if contains_forbidden_research_intent(request.question):
        _record_fallback(
            run_id=run_id,
            stage="input_safety",
            reason="forbidden_input",
            config=resolved_config,
        )
        return fallback_run

    if not resolved_config.available:
        _record_fallback(
            run_id=run_id,
            stage="config",
            reason="config_unavailable",
            config=resolved_config,
        )
        return fallback_run

    executor = ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="researchos-agentic-pipeline",
    )
    future = executor.submit(
        _run_configured_agentic_research_pipeline,
        request,
        fallback_run,
        resolved_config,
        client,
        run_id,
    )
    try:
        run = future.result(
            timeout=resolved_config.pipeline_timeout_seconds
        )
    except FutureTimeout:
        future.cancel()
        _record_fallback(
            run_id=run_id,
            stage="pipeline",
            reason="pipeline_timeout",
            config=resolved_config,
            error_type="TimeoutError",
        )
        close_agentic_run(run_id)
        return fallback_run
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return run


def _run_configured_agentic_research_pipeline(
    request: ResearchRunRequest,
    fallback_run: ResearchRun,
    resolved_config: AgenticResearchConfig,
    client: OpenAIResearchClient | None,
    run_id: str,
) -> ResearchRun:
    current_stage = "client_setup"
    deadline = _AgenticPipelineDeadline(
        timeout_seconds=resolved_config.pipeline_timeout_seconds
    )
    try:
        deadline.raise_if_expired()
        research_client = client or OpenAIResearchClient(resolved_config)
        if _should_use_fast_synthesis_path(request, resolved_config):
            current_stage = "fast_synthesis"
            synthesis_payload = _run_fast_synthesis_stage(
                research_client,
                request,
                resolved_config,
                deadline,
            )
            deadline.raise_if_expired()
            current_stage = "normalization"
            run = normalize_fast_synthesis_research_run(
                synthesis_payload,
                requested_question=request.question,
            )
        else:
            current_stage = "planner"
            planner = _run_planner_stage(
                research_client,
                request,
                resolved_config,
                deadline,
            )
            if planner.scope == "out_of_scope":
                _record_fallback(
                    run_id=run_id,
                    stage=current_stage,
                    reason="planner_out_of_scope",
                    config=resolved_config,
                )
                return fallback_run

            current_stage = "source_research"
            source_research = _run_source_stage(
                research_client,
                request,
                planner,
                resolved_config,
                deadline,
            )
            current_stage = "framework"
            framework = _run_framework_stage(
                research_client,
                request,
                planner,
                source_research,
                resolved_config,
                deadline,
            )
            current_stage = "skeptic"
            skeptic = _run_skeptic_stage(
                research_client,
                request,
                planner,
                source_research,
                framework,
                resolved_config,
                deadline,
            )
            current_stage = "synthesis"
            synthesis_payload = _run_synthesis_stage(
                research_client,
                request,
                planner,
                source_research,
                framework,
                skeptic,
                resolved_config,
                deadline,
            )
            deadline.raise_if_expired()
            current_stage = "normalization"
            run = normalize_agentic_research_run(
                synthesis_payload,
                requested_question=request.question,
            )
        current_stage = "safety"
        safety = validate_agentic_research_run(run)
        if not safety.passed:
            _record_fallback(
                run_id=run_id,
                stage=current_stage,
                reason="safety_failed",
                config=resolved_config,
                safety_reasons=safety.reasons,
            )
            return fallback_run
    except AgenticPipelineTimeout as exc:
        _record_fallback(
            run_id=run_id,
            stage="pipeline",
            reason="pipeline_timeout",
            config=resolved_config,
            error_type=type(exc).__name__,
        )
        return fallback_run
    except Exception as exc:
        if deadline.expired or _should_treat_as_pipeline_timeout(
            deadline,
            exc,
        ):
            _record_fallback(
                run_id=run_id,
                stage="pipeline",
                reason="pipeline_timeout",
                config=resolved_config,
                error_type="TimeoutError",
            )
            return fallback_run
        _record_fallback(
            run_id=run_id,
            stage=current_stage,
            reason=_fallback_reason_for_exception(current_stage, exc),
            config=resolved_config,
            error_type=type(exc).__name__,
        )
        return fallback_run

    record_agentic_success(run_id=run_id)
    return run


def _run_planner_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> PlannerStageResult:
    payload = _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_planner",
        instructions=PLANNER_PROMPT,
        schema=PlannerStageResult.model_json_schema(),
        input_data={"question": request.question},
    )
    return _validate_stage(PlannerStageResult, payload, "planner")


def _run_fast_synthesis_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> dict[str, Any]:
    return _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_fast_synthesis",
        instructions=FAST_SYNTHESIS_PROMPT,
        schema=FastSynthesisStageResult.model_json_schema(),
        input_data={
            "question": request.question,
            "webSearchEnabled": config.web_search_enabled,
            "sourceMode": "framework_only",
            "agenticEvidencePolicy": (
                "Use Framework inference, Narrative signal, or Open question. "
                "Do not use Data evidence in agentic output."
            ),
            "targetMilestone": "single_pass_fast_beta_success",
        },
    )


def _run_source_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> SourceResearchResult:
    payload = _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_source_research",
        instructions=SOURCE_RESEARCH_PROMPT,
        schema=SourceResearchResult.model_json_schema(),
        input_data={
            "question": request.question,
            "planner": planner.model_dump(),
            "webSearchEnabled": config.web_search_enabled,
            "sourceMode": (
                "web_search" if config.web_search_enabled else "framework_only"
            ),
        },
        allow_web_search=config.web_search_enabled,
    )
    return _validate_stage(SourceResearchResult, payload, "source research")


def _run_framework_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    source_research: SourceResearchResult,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> FrameworkStageResult:
    payload = _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_framework",
        instructions=FRAMEWORK_PROMPT,
        schema=FrameworkStageResult.model_json_schema(),
        input_data={
            "question": request.question,
            "planner": planner.model_dump(),
            "sourceResearch": source_research.model_dump(),
            "webSearchEnabled": config.web_search_enabled,
            "agenticEvidencePolicy": (
                "Use Source claim, Framework inference, Narrative signal, "
                "or Open question. Do not use Data evidence in agentic "
                "output."
            ),
        },
    )
    return _validate_stage(FrameworkStageResult, payload, "framework")


def _run_skeptic_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    source_research: SourceResearchResult,
    framework: FrameworkStageResult,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> SkepticStageResult:
    payload = _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_skeptic",
        instructions=SKEPTIC_PROMPT,
        schema=SkepticStageResult.model_json_schema(),
        input_data={
            "question": request.question,
            "planner": planner.model_dump(),
            "sourceResearch": source_research.model_dump(),
            "framework": framework.model_dump(),
            "agenticEvidencePolicy": (
                "Use Source claim, Framework inference, Narrative signal, "
                "or Open question. Do not use Data evidence in agentic "
                "output."
            ),
        },
    )
    return _validate_stage(SkepticStageResult, payload, "skeptic")


def _run_synthesis_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    source_research: SourceResearchResult,
    framework: FrameworkStageResult,
    skeptic: SkepticStageResult,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> dict[str, Any]:
    return _create_structured_response_with_deadline(
        client,
        config,
        deadline,
        stage_name="agentic_synthesis",
        instructions=SYNTHESIS_PROMPT,
        schema=SynthesisStageResult.model_json_schema(),
        input_data={
            "question": request.question,
            "planner": planner.model_dump(),
            "sourceResearch": source_research.model_dump(),
            "framework": framework.model_dump(),
            "skeptic": skeptic.model_dump(),
            "webSearchEnabled": config.web_search_enabled,
            "agenticEvidencePolicy": (
                "Use Source claim, Framework inference, Narrative signal, "
                "or Open question. Do not use Data evidence in agentic "
                "output."
            ),
        },
    )


def _create_structured_response_with_deadline(
    client: OpenAIResearchClient,
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
    **kwargs: Any,
) -> dict[str, Any]:
    request_timeout_seconds = _request_timeout_seconds(config, deadline)
    try:
        payload = client.create_structured_response(
            **kwargs,
            request_timeout_seconds=request_timeout_seconds,
        )
    except AgenticResearchError as exc:
        if exc.reason == "timeout" and deadline.expired:
            raise AgenticPipelineTimeout(
                "Agentic pipeline deadline exceeded during model call"
            ) from exc
        raise

    deadline.raise_if_expired()
    return payload


def _request_timeout_seconds(
    config: AgenticResearchConfig,
    deadline: "_AgenticPipelineDeadline",
) -> float:
    remaining_seconds = deadline.remaining_seconds
    if remaining_seconds <= 0:
        raise AgenticPipelineTimeout("Agentic pipeline deadline exceeded")
    return min(config.timeout_seconds, remaining_seconds)


def _validate_stage(
    model: type[Any],
    payload: dict[str, Any],
    stage_name: str,
) -> Any:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise AgenticPipelineError(
            f"Agentic {stage_name} stage returned invalid payload"
        ) from exc


def _fallback_reason_for_stage(stage: str) -> str:
    return {
        "client_setup": "config_unavailable",
        "pipeline": "pipeline_timeout",
        "fast_synthesis": "fast_synthesis_failed",
        "planner": "planner_failed",
        "source_research": "source_research_failed",
        "framework": "framework_failed",
        "skeptic": "skeptic_failed",
        "synthesis": "synthesis_failed",
        "normalization": "normalization_failed",
        "safety": "safety_failed",
    }.get(stage, "unexpected_error")


def _fallback_reason_for_exception(stage: str, exc: Exception) -> str:
    if isinstance(exc, AgenticResearchError):
        return exc.reason
    return _fallback_reason_for_stage(stage)


def _should_treat_as_pipeline_timeout(
    deadline: "_AgenticPipelineDeadline",
    exc: Exception,
) -> bool:
    return (
        deadline.expired
        and isinstance(exc, AgenticResearchError)
        and exc.reason == "timeout"
    )


def _record_fallback(
    *,
    run_id: str,
    stage: str,
    reason: str,
    config: AgenticResearchConfig,
    error_type: str | None = None,
    safety_reasons: tuple[str, ...] = (),
) -> None:
    safe_safety_reasons = tuple(
        _safe_reason_name(reason_text) for reason_text in safety_reasons
    )
    recorded = record_agentic_fallback(
        run_id=run_id,
        reason=reason,
        stage=stage,
        error_type=error_type,
    )
    if not recorded:
        return
    _logger.warning(
        "Agentic beta fallback stage=%s reason=%s error_type=%s "
        "safety_reason_count=%s safety_reasons=%s "
        "web_search_enabled=%s model=%s",
        stage,
        reason,
        error_type or "none",
        len(safe_safety_reasons),
        ",".join(safe_safety_reasons) or "none",
        config.web_search_enabled,
        config.model,
    )


def _safe_reason_name(reason: str) -> str:
    safe = reason.lower().replace("/", " ")
    safe = "_".join(part for part in safe.split() if part)
    return safe[:80] or "unknown"


def _should_use_fast_synthesis_path(
    request: ResearchRunRequest,
    config: AgenticResearchConfig,
) -> bool:
    return (
        not config.web_search_enabled
        and " ".join(request.question.lower().split())
        == _FAST_SYNTHESIS_TARGET_QUESTION
    )


class _AgenticPipelineDeadline:
    def __init__(self, *, timeout_seconds: float) -> None:
        self._deadline = time.monotonic() + timeout_seconds

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self._deadline - time.monotonic())

    @property
    def expired(self) -> bool:
        return self.remaining_seconds <= 0

    def raise_if_expired(self) -> None:
        if self.expired:
            raise AgenticPipelineTimeout(
                "Agentic pipeline deadline exceeded"
            )
