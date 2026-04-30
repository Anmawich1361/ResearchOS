from pydantic import ValidationError

from app.agentic.models import SynthesisStageResult
from app.schemas import ResearchRun


class AgenticNormalizationError(ValueError):
    pass


def normalize_agentic_research_run(
    payload: dict[str, object],
    *,
    requested_question: str,
) -> ResearchRun:
    try:
        synthesis = SynthesisStageResult.model_validate(payload)
    except ValidationError as exc:
        raise AgenticNormalizationError(
            "Agentic synthesis payload did not match ResearchRun schema"
        ) from exc

    run = synthesis.researchRun
    question = requested_question.strip()
    if question:
        run = run.model_copy(update={"question": question})

    return run
