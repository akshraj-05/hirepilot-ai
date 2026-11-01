# """Pydantic models for the Insight Agent — inputs and structured output."""

# from typing import Literal

# from pydantic import BaseModel, Field


# # ---------------------------------------------------------------------------
# # Input models
# # ---------------------------------------------------------------------------


# class CandidateDecision(BaseModel):
#     """Screening result for a single candidate as produced by the Decision Agent."""

#     candidate_id: str
#     job_id: str
#     role_title: str
#     match_score: float = Field(..., ge=0, le=100)
#     skills_overlap_with_jd: list[str] = Field(default_factory=list)
#     skills_missing_from_resume: list[str] = Field(default_factory=list)
#     status: Literal["shortlist", "review", "reject"]
#     decision_reasons: list[str] = Field(default_factory=list)
#     override_status: str | None = None


# class HistoricalBatch(BaseModel):
#     """Aggregated screening metrics for a past hiring batch (RAG retrieval unit)."""

#     job_id: str
#     role_title: str
#     organization_name: str
#     avg_match_score: float
#     shortlist_rate: float = Field(..., ge=0, le=100)
#     top_missing_skills: list[str] = Field(default_factory=list)
#     strategic_patterns: list[str] = Field(default_factory=list)


# class RagResults(BaseModel):
#     """Historical retrieval context supplied to the Insight Agent."""

#     similar_past_batches: list[HistoricalBatch] = Field(default_factory=list)


# class InsightAnalysisMetadata(BaseModel):
#     """Mode selector and context envelope for the insight run."""

#     mode: Literal["job_level", "org_level"]
#     organization_name: str = Field(..., min_length=1)
#     job_id: str | None = Field(
#         default=None,
#         description="Required in job_level mode; must be null in org_level mode.",
#     )
#     jd_text: str | None = Field(
#         default=None,
#         description="Full JD text; required in job_level mode.",
#     )


# # ---------------------------------------------------------------------------
# # Output models
# # ---------------------------------------------------------------------------


# class InsightItem(BaseModel):
#     """A single insight — either a skill-gap finding or a strategic observation."""

#     category: Literal["skill_gap", "strategic_note"]
#     skill_name: str | None = Field(
#         default=None,
#         description="Populated for skill_gap; null for strategic_note.",
#     )
#     affected_count: int | None = Field(
#         default=None,
#         description="Candidates affected; null for strategic_note.",
#     )
#     percentage: float | None = Field(
#         default=None,
#         description="Percentage of pool affected; null for strategic_note.",
#     )
#     insight: str = Field(..., description="Data-grounded observation with business context.")
#     recommendation: str = Field(..., description="Specific, actionable next step.")


# class InsightReport(BaseModel):
#     """Structured output returned by the Insight Agent."""

#     mode: Literal["job_level", "org_level"]
#     job_id: str | None = None
#     organization_name: str
#     total_candidates_analyzed: int
#     shortlist_rate: float = Field(..., description="Percentage of shortlisted candidates in this batch.")
#     historical_shortlist_rate_avg: float | None = Field(
#         default=None,
#         description="Average shortlist rate across similar past batches; null if unavailable.",
#     )
#     insights: list[InsightItem] = Field(
#         default_factory=list,
#         description="3–5 skill_gap + 2–3 strategic_note entries (only above the 50% threshold).",
#     )
