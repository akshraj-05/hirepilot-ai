"""Decision Maker sub-agent — mutates state["decision_maker"] in place."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from app.agents.decision_maker import decisions_list_from_parsed, run_decision_maker_agent
from app.agents.state import OrchestratorState
from app.chroma.collections import get_assessments_collection, get_decisions_collection
from app.db import crud
from app.db.engine import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DecisionMaker:
    def _upsert_candidate_assessments_to_chroma(
        self,
        organization_id: str,
        job_id: str,
        candidate_ids: list[str],
        assessment_texts: list[str],
    ) -> None:
        """One embedded assessment per (candidate, job) — mirrors resume text in candidates collection."""
        if not job_id or not candidate_ids:
            return
        if len(candidate_ids) != len(assessment_texts):
            logger.warning(
                "Assessment batch length mismatch: %s candidates vs %s analyses",
                len(candidate_ids),
                len(assessment_texts),
            )
            return
        try:
            col = get_assessments_collection()
            ids = [f"{cid}__{job_id}" for cid in candidate_ids]
            documents = [t.strip() if t else "(empty assessment)" for t in assessment_texts]
            metadatas = [
                {"candidate_id": cid, "job_id": job_id, "org_id": organization_id}
                for cid in candidate_ids
            ]
            col.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as e:
            logger.warning("Chroma assessment upsert failed (continuing without vector store): %s", e)

    @staticmethod
    def _decision_document_text_for_chroma(row: dict[str, Any]) -> str:
        status = row.get("status") or ""
        score = row.get("match_score", 0)
        reasons_list = row.get("decision_reasons") or []
        if isinstance(reasons_list, str):
            reasons = reasons_list
        else:
            reasons = " ".join(str(x) for x in reasons_list)
        overlap = row.get("skills_overlap_with_jd") or []
        missing = row.get("skills_missing_from_resume") or []
        if isinstance(overlap, str):
            ov = overlap
        else:
            ov = ", ".join(str(x) for x in overlap)
        if isinstance(missing, str):
            ms = missing
        else:
            ms = ", ".join(str(x) for x in missing)
        return (
            f"status: {status} | score: {score} | reasons: {reasons} | "
            f"matched: {ov} | missing: {ms}"
        )

    async def _upsert_decisions_to_chroma(
        self,
        parsed: Any,
        organization_id: str,
        job_id: str,
        role_title: str,
    ) -> None:
        """Persist decisions to ChromaDB and simultaneously insert into PostgreSQL decision_maker table."""
        if not job_id:
            return
        if isinstance(parsed, list):
            rows = [r for r in parsed if isinstance(r, dict)]
        elif isinstance(parsed, dict):
            rows = [parsed]
        else:
            return
        if not rows:
            return

        # --- ChromaDB ---
        try:
            col = get_decisions_collection()
        except Exception as e:
            logger.warning("Chroma decisions collection unavailable: %s", e)
            col = None

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for row in rows:
            cid = row.get("candidate_id")
            if not cid:
                continue
            doc_id = f"{cid}__{job_id}"
            ids.append(doc_id)
            documents.append(self._decision_document_text_for_chroma(row))
            reasons = row.get("decision_reasons") or []
            if isinstance(reasons, str):
                dr = reasons
            else:
                dr = "|".join(str(x) for x in reasons)
            overlap = row.get("skills_overlap_with_jd") or []
            missing = row.get("skills_missing_from_resume") or []
            if isinstance(overlap, str):
                so = overlap
            else:
                so = "|".join(str(x) for x in overlap)
            if isinstance(missing, str):
                sm = missing
            else:
                sm = "|".join(str(x) for x in missing)
            score = row.get("match_score", 0.0)
            try:
                ms = float(score)
            except (TypeError, ValueError):
                ms = 0.0
            metadatas.append(
                {
                    "candidate_id": str(cid),
                    "job_id": job_id,
                    "org_id": organization_id,
                    "role_title": role_title,
                    "status": str(row.get("status") or ""),
                    "match_score": ms,
                    "decision_reasons": dr,
                    "skills_overlap": so,
                    "skills_missing": sm,
                }
            )

        if ids and col is not None:
            try:
                col.upsert(ids=ids, documents=documents, metadatas=metadatas)
            except Exception as e:
                logger.warning("Chroma decision upsert failed: %s", e)

        # --- PostgreSQL decision_maker table ---
        try:
            org_uuid = uuid.UUID(organization_id)
        except ValueError:
            logger.warning("Invalid organization_id UUID, skipping PostgreSQL save: %s", organization_id)
            return

        async with AsyncSessionLocal() as db:
            for row in rows:
                cid_str = row.get("candidate_id")
                if not cid_str:
                    continue
                try:
                    cid_uuid = uuid.UUID(str(cid_str))
                except ValueError:
                    continue

                score = row.get("match_score", 0.0)
                try:
                    score = float(score)
                except (TypeError, ValueError):
                    score = 0.0

                reasons = row.get("decision_reasons") or []
                if isinstance(reasons, str):
                    reasons = [r.strip() for r in reasons.split("|") if r.strip()]

                overlap = row.get("skills_overlap_with_jd") or []
                if isinstance(overlap, str):
                    overlap = [s.strip() for s in overlap.split("|") if s.strip()]

                missing = row.get("skills_missing_from_resume") or []
                if isinstance(missing, str):
                    missing = [s.strip() for s in missing.split("|") if s.strip()]

                status = str(row.get("status") or "review").lower()

                try:
                    existing = await crud.decision_maker.get_by_candidate_and_job(db, cid_uuid, job_id)
                    if existing:
                        await crud.decision_maker.update(
                            db,
                            existing.id,
                            match_score=score,
                            skills_overlap_with_jd=overlap,
                            skills_missing_from_resume=missing,
                            status=status,
                            decision_reasons=reasons,
                        )
                    else:
                        await crud.decision_maker.create(
                            db,
                            org_id=org_uuid,
                            candidate_id=cid_uuid,
                            posted_job_id=job_id,
                            match_score=score,
                            skills_overlap_with_jd=overlap,
                            skills_missing_from_resume=missing,
                            status=status,
                            decision_reasons=reasons,
                        )
                except Exception:
                    logger.exception("Failed to save decision for candidate %s to PostgreSQL", cid_str)

    async def run(self, state: OrchestratorState) -> None:
        state["decision_maker"]["status"] = "inprogress"

        try:
            org_id = state["organization_id"]
            async with AsyncSessionLocal() as db:
                job = await crud.job_postings.get(db, state["job_id"])
            jd = str(job.description if job else "") or ""
            role_title = str(job.role if job else "") or ""
            assessment_json = json.dumps(
                [
                    {"candidate_id": cid, "resume_analysis": a}
                    for cid, a in zip(
                        state["candidates"],
                        state["resume_analyzer"]["analyzed_candidates"],
                    )
                ],
                indent=2,
            )
            self._upsert_candidate_assessments_to_chroma(
                org_id,
                state["job_id"],
                state["candidates"],
                state["resume_analyzer"]["analyzed_candidates"],
            )
            parsed = await run_decision_maker_agent(
                job_description=jd,
                candidate_resume_assessment_json=assessment_json,
                organization_id=org_id,
                job_id=state["job_id"],
                exclude_candidate_ids=state["candidates"],
            )
            await self._upsert_decisions_to_chroma(
                parsed,
                org_id,
                state["job_id"],
                role_title,
            )
            state["decision_maker"]["decisions"] = decisions_list_from_parsed(parsed)
            state["decision_maker"]["status"] = "completed"

        except Exception as e:
            state["decision_maker"]["status"] = "failed"
            state["decision_maker"]["decisions"] = []
            raise RuntimeError(f"DecisionMaker failed: {e}") from e
