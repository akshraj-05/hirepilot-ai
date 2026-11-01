# """Insight Agent endpoint — job-level and org-level hiring analysis."""

# import logging

# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field, model_validator
# from typing import Optional

# logger = logging.getLogger(__name__)

# from app.config import settings
# from app.schemas.insight import (
#     CandidateDecision,
#     InsightAnalysisMetadata,
#     InsightReport,
#     RagResults,
# )
# from app.agents.sub_agents.insight_agent import run_insight_agent

# router = APIRouter(prefix="/insights", tags=["insights"])


# # ---------------------------------------------------------------------------
# # Request body
# # ---------------------------------------------------------------------------


# class InsightRequest(BaseModel):
#     """
#     Request envelope for the Insight Agent.

#     Accepts two shapes:
#     1. Nested  — { "metadata": { "mode": ..., "job_id": ..., ... }, "candidates": [...] }
#     2. Flat    — { "mode": ..., "job_id": ..., "organization_name": ..., "candidates": [...] }
#        Flat fields are promoted into a `metadata` object automatically.

#     `candidates` and `rag_results` are always optional:
#     - Omit `candidates`      → auto-collected from stored screening results.
#     - Omit `rag_results`     → auto-built from historical data in storage.
#     - Omit `organization_id` → required only when candidates are not supplied.
#     """

#     metadata: InsightAnalysisMetadata
#     organization_id: Optional[str] = Field(
#         None,
#         min_length=1,
#         description="Internal org key used to scope storage queries.",
#     )
#     candidates: list[CandidateDecision] | None = Field(
#         default=None,
#         description="Pre-built candidate decision objects. Omit to auto-collect from storage.",
#     )
#     rag_results: RagResults | None = Field(
#         default=None,
#         description="Pre-built RAG retrieval context. Omit to auto-build from historical data.",
#     )

#     @model_validator(mode="before")
#     @classmethod
#     def _promote_flat_fields(cls, values: dict) -> dict:
#         """
#         Accept flat payloads where mode / job_id / organization_name sit at the
#         top level instead of inside a nested `metadata` object.  Output-only
#         fields (total_candidates_analyzed, shortlist_rate, etc.) are silently
#         dropped so callers can round-trip the response schema as a request.

#         organization_id and candidates are already at the correct top level and
#         are left untouched.  If neither is present the `_validate_mode_fields`
#         validator below will surface a clear error.
#         """
#         if isinstance(values, dict) and "metadata" not in values and "mode" in values:
#             values["metadata"] = {
#                 "mode": values.pop("mode", None),
#                 "organization_name": values.pop("organization_name", ""),
#                 "job_id": values.pop("job_id", None),
#                 "jd_text": values.pop("jd_text", None),
#             }
#             # Drop output-only fields that callers sometimes include.
#             for output_field in (
#                 "total_candidates_analyzed",
#                 "shortlist_rate",
#                 "historical_shortlist_rate_avg",
#                 "insights",
#             ):
#                 values.pop(output_field, None)
#         return values

#     @model_validator(mode="after")
#     def _validate_mode_fields(self) -> "InsightRequest":
#         if self.metadata.mode == "job_level":
#             if not self.metadata.job_id:
#                 raise ValueError("job_id is required for job_level mode.")
#         if self.metadata.mode == "org_level":
#             if self.metadata.job_id is not None:
#                 raise ValueError("job_id must be null in org_level mode.")
#             if self.metadata.jd_text is not None:
#                 raise ValueError("jd_text must be null in org_level mode.")
#         if not self.organization_id and not self.candidates:
#             raise ValueError(
#                 "Provide either organization_id (to auto-collect candidates from storage) "
#                 "or an explicit candidates list."
#             )
#         return self


# # ---------------------------------------------------------------------------
# # Routes
# # ---------------------------------------------------------------------------
# @router.post(
#     "",
#     response_model=InsightReport,
#     summary="Run Insight Agent",
#     description=(
#         "Analyze screened candidates for a single job (job_level) or across all "
#         "active roles for an organization (org_level). Returns structured skill-gap "
#         "findings and strategic hiring observations backed by historical comparison."
#     ),
# )
# def generate_insights(body: InsightRequest) -> InsightReport:
#     if not settings.openai_api_key:
#         raise HTTPException(
#             status_code=503,
#             detail="OPENAI_API_KEY is not set — add it to .env to enable the Insight Agent.",
#         )

#     try:
#         return run_insight_agent(
#             metadata=body.metadata,
#             candidates=body.candidates,
#             rag_results=body.rag_results,
#             organization_id=body.organization_id or "",
#         )
#     except Exception as exc:
#         logger.exception("Unexpected error running insight agent")
#         raise HTTPException(
#             status_code=502,
#             detail=f"Insight analysis failed. Please try again later.",
#         ) from exc
