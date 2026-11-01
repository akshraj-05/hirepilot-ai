"""Orchestrator — creates state once and drives sub-agents sequentially."""

import logging
from typing import List

from app.agents.state import ModeType, OrchestratorState, build_initial_state
from app.agents.sub_agents.resume_analyzer import ResumeAnalyzer
from app.agents.sub_agents.decision_maker import DecisionMaker
from app.agents.sub_agents.insight_agent import InsightAgent

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self):
        self.resume_analyzer = ResumeAnalyzer()
        self.decision_maker = DecisionMaker()
        self.insight_agent = InsightAgent()

    async def run(
        self,
        job_id: str,
        candidates: List[str],
        organization_id: str,
        organization_name: str,
        mode: ModeType = "job_level",
    ) -> OrchestratorState:
        """
        Creates a single OrchestratorState and passes it through each sub-agent.
        Sub-agents mutate the state in place — no new state objects are created.
        Stage 1 (ResumeAnalyzer) is mandatory; later stages are best-effort.
        """
        state: OrchestratorState = build_initial_state(
            job_id=job_id,
            candidates=candidates,
            organization_id=organization_id,
            organization_name=organization_name,
            mode=mode,
        )

        # Stage 1: Resume Analysis — mandatory; failure here aborts the pipeline
        await self.resume_analyzer.run(state)
        if state["resume_analyzer"]["status"] == "failed" or not state["resume_analyzer"]["analyzed_candidates"]:
            state["resume_analyzer"]["status"] = "failed"
            raise RuntimeError("ResumeAnalyzer failed or produced no results — aborting pipeline.")

        # Stage 2: Decision Making — best-effort; failure is logged, not fatal
        try:
            await self.decision_maker.run(state)
            if state["decision_maker"]["status"] == "failed" or not state["decision_maker"]["decisions"]:
                state["decision_maker"]["status"] = "failed"
                log.warning("DecisionMaker produced no decisions — continuing without.")
        except Exception as exc:
            state["decision_maker"]["status"] = "failed"
            log.warning("DecisionMaker failed: %s — continuing without.", exc)

        # Stage 3: Insight Generation — best-effort; only runs if decisions exist
        if state["decision_maker"]["status"] != "failed":
            try:
                await self.insight_agent.run(state)
            except Exception as exc:
                state["insight_agent"]["status"] = "failed"
                log.warning("InsightAgent failed: %s — continuing without.", exc)

        return state
