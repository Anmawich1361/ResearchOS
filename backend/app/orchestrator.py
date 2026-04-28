from app.agents import (
    run_data_agent,
    run_framework_agent,
    run_planner,
    run_skeptic_agent,
    run_synthesis_agent,
)
from app.schemas import ResearchRun, ResearchRunRequest


def run_research_pipeline(request: ResearchRunRequest) -> ResearchRun:
    plan = run_planner(request.question)
    data = run_data_agent(plan)
    framework = run_framework_agent(plan, data)
    skeptic = run_skeptic_agent(plan, data, framework)
    synthesis = run_synthesis_agent(plan, data, framework, skeptic)

    return ResearchRun(
        question=plan.question,
        classification=plan.classification,
        timestamp=plan.timestamp,
        scenario=plan.scenario,
        headline=synthesis.headline,
        thesis=synthesis.thesis,
        judgment=synthesis.judgment,
        keyDrivers=plan.keyDrivers,
        metrics=data.metrics,
        agents=[
            plan.stage,
            data.stage,
            framework.stage,
            skeptic.stage,
            synthesis.stage,
        ],
        transmissionNodes=framework.transmissionNodes,
        transmissionEdges=framework.transmissionEdges,
        charts=data.charts,
        evidence=[
            *framework.evidence[:3],
            *data.evidence,
            *framework.evidence[3:],
            *synthesis.evidence,
            *skeptic.evidence,
        ],
        bullCase=synthesis.bullCase,
        bearCase=skeptic.bearCase,
        memo=synthesis.memo,
        openQuestions=skeptic.openQuestions,
    )
