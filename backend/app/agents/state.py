"""Single source of truth for all agent state types."""

from typing import TypedDict, List, Literal

StatusType = Literal["pending", "inprogress", "completed", "failed"]
ModeType = Literal["job_level", "org_level"]


class ResumeAnalyzerState(TypedDict):
    status: StatusType
    analyzed_candidates: List[str]


class DecisionMakerState(TypedDict):
    status: StatusType
    decisions: List[dict]  # structured candidate decision objects


class InsightAgentState(TypedDict):
    status: StatusType
    insights: dict  # full InsightReport JSON object from the LLM


class OrchestratorState(TypedDict):
    job_id: str
    organization_id: str
    organization_name: str
    mode: ModeType
    candidates: List[str]
    resume_analyzer: ResumeAnalyzerState
    decision_maker: DecisionMakerState
    insight_agent: InsightAgentState


def build_initial_state(
    job_id: str,
    candidates: List[str],
    organization_id: str,
    organization_name: str,
    mode: ModeType = "job_level",
) -> OrchestratorState:
    """Build a fresh OrchestratorState — called once by the orchestrator."""
    return OrchestratorState(
        job_id=job_id or "",
        organization_id=organization_id,
        organization_name=organization_name,
        mode=mode,
        candidates=candidates,
        resume_analyzer=ResumeAnalyzerState(status="pending", analyzed_candidates=[]),
        decision_maker=DecisionMakerState(status="pending", decisions=[]),
        insight_agent=InsightAgentState(status="pending", insights={}),
    )
