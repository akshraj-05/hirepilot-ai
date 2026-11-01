"""Insight Agent — generates hiring insights from batch decisions + ChromaDB history."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from langchain_core.prompts import PromptTemplate

from app.agents.llm import get_agent_llm
from app.agents.state import OrchestratorState
from app.agents.prompt.insight_agent_prompt import INSIGHT_AGENT_PROMPT
from app.chroma.collections import get_decisions_collection, get_insights_collection
from app.db import crud
from app.db.engine import AsyncSessionLocal

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = INSIGHT_AGENT_PROMPT + """

════════════════════════════════════════════════════════════════
INPUT DATA
════════════════════════════════════════════════════════════════

Metadata:
{metadata_json}

Current Batch Candidates:
{candidates_json}

Historical Context:
{historical_json}
"""


class InsightAgent:
    def __init__(self):
        self.chain = PromptTemplate.from_template(_PROMPT_TEMPLATE) | get_agent_llm()

    async def run(self, state: OrchestratorState) -> None:
        state["insight_agent"]["status"] = "inprogress"

        try:
            decisions: list[dict] = state["decision_maker"]["decisions"]
            historical = self._fetch_historical(state)

            metadata = {
                "mode": state["mode"],
                "job_id": state["job_id"] if state["mode"] == "job_level" else None,
                "organization_name": state["organization_name"],
            }

            result = await self.chain.ainvoke({
                "metadata_json": json.dumps(metadata, indent=2),
                "candidates_json": json.dumps(decisions, indent=2),
                "historical_json": json.dumps(historical, indent=2),
            })

            raw = result.content.strip()
            insights_report: dict = self._extract_json(raw)

            await self._store_insights(state, insights_report)

            state["insight_agent"]["insights"] = insights_report
            state["insight_agent"]["status"] = "completed"

        except Exception as e:
            state["insight_agent"]["status"] = "failed"
            state["insight_agent"]["insights"] = {}
            raise RuntimeError(f"InsightAgent failed: {e}") from e

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from LLM output that may contain prose or code fences."""
        import re
        # Try a ```json ... ``` block first
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # Fall back: find the first { ... } spanning the whole structure
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("No JSON object found in LLM response")

    # ------------------------------------------------------------------
    # ChromaDB + PostgreSQL helpers
    # ------------------------------------------------------------------

    def _fetch_historical(self, state: OrchestratorState) -> dict:
        """
        Query the decisions collection for past batches.

        job_level  → filter by job_id, exclude current-batch candidate IDs.
        org_level  → filter by org_id across all jobs.
        """
        try:
            col = get_decisions_collection()
            current_candidate_ids = {
                d["candidate_id"]
                for d in state["decision_maker"]["decisions"]
                if "candidate_id" in d
            }

            if state["mode"] == "job_level":
                where = {"job_id": state["job_id"]}
            else:
                where = {"org_id": state["organization_id"]}

            result = col.get(where=where, include=["metadatas", "documents"])
            metadatas = result.get("metadatas") or []

            # Exclude candidates that are part of the current batch
            past = [m for m in metadatas if m.get("candidate_id") not in current_candidate_ids]

            if not past:
                return {"similar_past_batches": []}

            # Group by job_id to form batch summaries
            batches: dict[str, list[dict]] = {}
            for m in past:
                jid = m.get("job_id", "unknown")
                batches.setdefault(jid, []).append(m)

            similar_past_batches = []
            for jid, records in batches.items():
                total = len(records)
                shortlisted = sum(1 for r in records if r.get("status") == "shortlist")
                shortlist_rate = round((shortlisted / total) * 100, 1) if total else 0

                all_missing: list[str] = []
                patterns: list[str] = []
                for r in records:
                    skills_missing = r.get("skills_missing", "")
                    if skills_missing:
                        all_missing.extend(s.strip() for s in skills_missing.split("|") if s.strip())
                    reason = r.get("decision_reasons", "")
                    if reason:
                        patterns.extend(s.strip() for s in reason.split("|") if s.strip())

                # Top 5 most-common missing skills
                from collections import Counter
                top_missing = [skill for skill, _ in Counter(all_missing).most_common(5)]
                top_patterns = [p for p, _ in Counter(patterns).most_common(3)]

                similar_past_batches.append({
                    "job_id": jid,
                    "role_title": records[0].get("role_title", ""),
                    "organization_name": state["organization_name"],
                    "avg_match_score": round(
                        sum(float(r.get("match_score", 0)) for r in records) / total, 1
                    ),
                    "shortlist_rate": shortlist_rate,
                    "top_missing_skills": top_missing,
                    "strategic_patterns": top_patterns,
                })

            return {"similar_past_batches": similar_past_batches}

        except Exception:
            # Historical data is best-effort — don't fail the whole run
            return {"similar_past_batches": []}

    async def _store_insights(self, state: OrchestratorState, report: dict) -> None:
        """Upsert insight report into ChromaDB and simultaneously insert rows into PostgreSQL ai_insights."""
        # --- ChromaDB ---
        try:
            col = get_insights_collection()
            scope = state["job_id"] if state["mode"] == "job_level" else state["organization_id"]
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            doc_id = f"{scope}__{ts}__{uuid.uuid4().hex[:6]}"

            insight_texts = [i.get("insight", "") for i in report.get("insights", [])]
            summary = (
                f"mode: {report.get('mode')} | "
                f"job_id: {report.get('job_id')} | "
                f"org: {report.get('organization_name')} | "
                f"shortlist_rate: {report.get('shortlist_rate')} | "
                f"insights: {' | '.join(insight_texts)}"
            )

            col.upsert(
                ids=[doc_id],
                documents=[summary],
                metadatas=[{
                    "job_id": state["job_id"] or "",
                    "org_id": state["organization_id"],
                    "organization_name": state["organization_name"],
                    "mode": state["mode"],
                    "shortlist_rate": float(report.get("shortlist_rate", 0)),
                    "total_candidates": int(report.get("total_candidates_analyzed", 0)),
                    "created_at": ts,
                    "insights_json": json.dumps(report),
                }],
            )
        except Exception as e:
            logger.warning("Chroma insights upsert failed: %s", e)

        # --- PostgreSQL ai_insights table ---
        insights = report.get("insights") or []
        if not insights:
            return

        try:
            org_uuid = uuid.UUID(state["organization_id"])
        except ValueError:
            logger.warning("Invalid organization_id UUID, skipping PostgreSQL save: %s", state["organization_id"])
            return

        job_id = state["job_id"] or None
        valid_categories = {"skill_gap", "strategic_note"}

        async with AsyncSessionLocal() as db:
            for item in insights:
                if not isinstance(item, dict):
                    continue
                category = str(item.get("category") or "strategic_note").lower()
                if category not in valid_categories:
                    category = "strategic_note"
                try:
                    await crud.ai_insights.create(
                        db,
                        org_id=org_uuid,
                        posted_job_id=job_id,
                        category=category,
                        insight=str(item.get("insight") or ""),
                        recommendation=str(item.get("recommendation") or ""),
                        skill_name=item.get("skill_name") or None,
                        affected_count=item.get("affected_count") or None,
                    )
                except Exception:
                    logger.exception("Failed to save insight to PostgreSQL: %s", item)
