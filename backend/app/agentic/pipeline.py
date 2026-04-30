from typing import Any

from pydantic import ValidationError

from app.agentic.config import (
    AgenticResearchConfig,
    get_agentic_research_config,
)
from app.agentic.models import (
    FrameworkStageResult,
    PlannerStageResult,
    SkepticStageResult,
    SourceResearchResult,
    SynthesisStageResult,
)
from app.agentic.normalizer import normalize_agentic_research_run
from app.agentic.openai_client import OpenAIResearchClient
from app.agentic.prompts import (
    FRAMEWORK_PROMPT,
    PLANNER_PROMPT,
    SKEPTIC_PROMPT,
    SOURCE_RESEARCH_PROMPT,
    SYNTHESIS_PROMPT,
)
from app.agentic.safety import validate_agentic_research_run
from app.orchestrator import run_research_pipeline
from app.schemas import ResearchRun, ResearchRunRequest


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

    if not resolved_config.available:
        return fallback_run

    try:
        research_client = client or OpenAIResearchClient(resolved_config)
        planner = _run_planner_stage(research_client, request)
        if planner.scope == "out_of_scope":
            return fallback_run

        source_research = _run_source_stage(
            research_client,
            request,
            planner,
            resolved_config,
        )
        framework = _run_framework_stage(
            research_client,
            request,
            planner,
            source_research,
        )
        skeptic = _run_skeptic_stage(
            research_client,
            request,
            planner,
            source_research,
            framework,
        )
        synthesis_payload = _run_synthesis_stage(
            research_client,
            request,
            planner,
            source_research,
            framework,
            skeptic,
        )
        run = normalize_agentic_research_run(
            synthesis_payload,
            requested_question=request.question,
        )
        safety = validate_agentic_research_run(
            run,
            verified_source_labels=_verified_source_labels(
                source_research,
                web_search_enabled=resolved_config.web_search_enabled,
            ),
        )
        if not safety.passed:
            return fallback_run
    except Exception:
        return fallback_run

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
        },
        allow_web_search=config.web_search_enabled,
    )
    return _validate_stage(SourceResearchResult, payload, "source research")


def _run_framework_stage(
    client: OpenAIResearchClient,
    request: ResearchRunRequest,
    planner: PlannerStageResult,
    source_research: SourceResearchResult,
) -> FrameworkStageResult:
    payload = client.create_structured_response(
        stage_name="agentic_framework",
        instructions=FRAMEWORK_PROMPT,
        schema=FrameworkStageResult.model_json_schema(),
        input_data={
            "question": request.question,
            "planner": planner.model_dump(),
            "sourceResearch": source_research.model_dump(),
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
        },
    )


def _verified_source_labels(
    source_research: SourceResearchResult,
    *,
    web_search_enabled: bool,
) -> set[str] | None:
    if not web_search_enabled:
        return None

    return {
        source_note.sourceLabel.strip()
        for source_note in source_research.sourceNotes
        if source_note.sourceLabel.strip()
    }


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
