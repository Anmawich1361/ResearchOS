import logging
from typing import Any

from pydantic import ValidationError

from app.agentic.config import (
    AgenticResearchConfig,
    get_agentic_research_config,
)
from app.agentic.diagnostics import (
    mark_agentic_run_started,
    record_agentic_fallback,
    record_agentic_success,
)
from app.agentic.models import (
    FrameworkStageResult,
    PlannerStageResult,
    SkepticStageResult,
    SourceResearchResult,
    SynthesisStageResult,
)
from app.agentic.normalizer import normalize_agentic_research_run
from app.agentic.openai_client import (
    AgenticResearchError,
    OpenAIResearchClient,
)
from app.agentic.prompts import (
    FRAMEWORK_PROMPT,
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


class AgenticPipelineError(RuntimeError):
    pass


def run_agentic_research_pipeline(
    request: ResearchRunRequest,
    *,
    config: AgenticResearchConfig | None = None,
    client: OpenAIResearchClient | None = None,
) -> ResearchRun:
    resolved_config = config or get_agentic_research_config()
    fallback_run = run_research_pipeline(request)
    mark_agentic_run_started()

    if contains_forbidden_research_intent(request.question):
        _record_fallback(
            stage="input_safety",
            reason="forbidden_input",
            config=resolved_config,
        )
        return fallback_run

    if not resolved_config.available:
        _record_fallback(
            stage="config",
            reason="config_unavailable",
            config=resolved_config,
        )
        return fallback_run

    current_stage = "client_setup"
    try:
        research_client = client or OpenAIResearchClient(resolved_config)
        current_stage = "planner"
        planner = _run_planner_stage(research_client, request)
        if planner.scope == "out_of_scope":
            _record_fallback(
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
        )
        current_stage = "framework"
        framework = _run_framework_stage(
            research_client,
            request,
            planner,
            source_research,
            resolved_config,
        )
        current_stage = "skeptic"
        skeptic = _run_skeptic_stage(
            research_client,
            request,
            planner,
            source_research,
            framework,
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
        )
        current_stage = "normalization"
        run = normalize_agentic_research_run(
            synthesis_payload,
            requested_question=request.question,
        )
        current_stage = "safety"
        safety = validate_agentic_research_run(run)
        if not safety.passed:
            _record_fallback(
                stage=current_stage,
                reason="safety_failed",
                config=resolved_config,
                safety_reasons=safety.reasons,
            )
            return fallback_run
    except Exception as exc:
        _record_fallback(
            stage=current_stage,
            reason=_fallback_reason_for_exception(current_stage, exc),
            config=resolved_config,
            error_type=type(exc).__name__,
        )
        return fallback_run

    record_agentic_success()
    return run


def _run_planner_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
) -> PlannerStageResult:
    payload = client.create_structured_response(
        stage_name="agentic_planner",
        instructions=PLANNER_PROMPT,
        schema=PlannerStageResult.model_json_schema(),
        input_data={"question": request.question},
    )
    return _validate_stage(PlannerStageResult, payload, "planner")


def _run_source_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    config: AgenticResearchConfig,
) -> SourceResearchResult:
    payload = client.create_structured_response(
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
) -> FrameworkStageResult:
    payload = client.create_structured_response(
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
) -> SkepticStageResult:
    payload = client.create_structured_response(
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
) -> dict[str, Any]:
    return client.create_structured_response(
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


def _record_fallback(
    *,
    stage: str,
    reason: str,
    config: AgenticResearchConfig,
    error_type: str | None = None,
    safety_reasons: tuple[str, ...] = (),
) -> None:
    safe_safety_reasons = tuple(
        _safe_reason_name(reason_text) for reason_text in safety_reasons
    )
    record_agentic_fallback(
        reason=reason,
        stage=stage,
        error_type=error_type,
    )
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
