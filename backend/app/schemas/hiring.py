"""Structured LLM outputs for match and decision flows."""

from pydantic import BaseModel, Field


class MatchAnalysis(BaseModel):
    match_score: int = Field(..., ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    summary: str = ""


class HiringDecisionResult(BaseModel):
    decision: str = Field(..., description="SHORTLIST, REJECT, or REVIEW")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = ""
