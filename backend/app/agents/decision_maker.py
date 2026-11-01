"""
Hiring Decision Agent — strategic candidate vs JD evaluation with RAG context.


Architecture
------------
1. RAG context — prefers ChromaDB semantic retrieval over historical decisions for this
   JD (same ``org_id`` + ``job_id``); falls back to in-memory APPLICATIONS peers.
2. build_decision_maker_user_message — JD + candidate assessment (from agents/prompt).
3. run_decision_maker_agent — ChatPromptTemplate (system + user), async ainvoke on the
   LLM, parses strict JSON output.

Chroma reads/writes for assessments and persisted decisions live on the DecisionMaker
sub-agent (same pattern as InsightAgent: collections + local helpers, no separate store module).

System and user prose live in ``app.agents.prompt.decision_maker_prompt``.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.agents.prompt.decision_maker_prompt import (
    DECISION_MAKER_SYSTEM_PROMPT,
    build_decision_maker_user_message,
)
from app.config import settings
from app.chroma.collections import get_decisions_collection
from app.storage import APPLICATIONS

logger = logging.getLogger(__name__)


def get_chat_model() -> ChatOpenAI:
    """Match ``insight_agent`` — OpenAI-compatible endpoint (e.g. Cerebras)."""
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_chat_model,
    )


_SYSTEM_PROMPT = DECISION_MAKER_SYSTEM_PROMPT

_USER_PROMPT = """\
{base_user_content}

## RAG RETRIEVAL RESULTS (similar decisions vs this JD)
{rag_json}


Respond with JSON only as specified in the system prompt.\
"""


def _build_decision_rag_from_storage(
    organization_id: str,
    job_id: str,
    exclude_candidate_ids: frozenset[str] | None = None,
) -> dict[str, Any]:
    """
    Peer screening rows for the same JD from APPLICATIONS (in-memory).

    *exclude_candidate_ids* omits candidates (e.g. current batch) so peers are
    historical / out-of-batch only when desired.

    Used when Chroma has no matching historical decisions for this job/org.
    Keep the return shape stable so prompts stay unchanged.
    """
    peers: list[dict[str, Any]] = []
    for (org_id, jid, cid), app in APPLICATIONS.items():
        if org_id != organization_id or jid != job_id:
            continue
        if exclude_candidate_ids is not None and cid in exclude_candidate_ids:
            continue
        peers.append(
            {
                "candidate_id": cid,
                "match_score": app.get("match_score"),
                "status": app.get("status"),
                "matched_skills": app.get("matched_skills", []),
                "missing_skills": app.get("missing_skills", []),
            }
        )
    return {"similar_decisions_same_jd": peers}


def _peer_row_from_chroma_decision_metadata(m: dict[str, Any]) -> dict[str, Any]:
    skills_overlap = str(m.get("skills_overlap") or "")
    skills_missing = str(m.get("skills_missing") or "")
    matched = [s.strip() for s in skills_overlap.split("|") if s.strip()]
    missing = [s.strip() for s in skills_missing.split("|") if s.strip()]
    score = m.get("match_score")
    try:
        match_score = float(score) if score is not None else None
    except (TypeError, ValueError):
        match_score = None
    return {
        "candidate_id": m.get("candidate_id"),
        "match_score": match_score,
        "status": m.get("status"),
        "matched_skills": matched,
        "missing_skills": missing,
    }


def _build_decision_rag_from_chroma(
    job_description: str,
    organization_id: str,
    job_id: str,
    *,
    exclude_candidate_ids: frozenset[str] | None = None,
    n_results: int = 12,
) -> dict[str, Any] | None:
    """
    Semantic retrieval over the decisions collection (JD as query text).
    Returns the same envelope as in-memory peer RAG, or None if unusable.
    """
    jd = job_description.strip()
    if not jd or not job_id:
        return None
    excluded = exclude_candidate_ids or frozenset()
    try:
        col = get_decisions_collection()
        fetch_n = max(n_results * 4, 24)
        res = col.query(
            query_texts=[jd],
            n_results=fetch_n,
            where={
                "$and": [
                    {"job_id": job_id},
                    {"org_id": organization_id},
                ]
            },
            include=["metadatas", "distances"],
        )
        batch = res.get("metadatas") or []
        if not batch or not batch[0]:
            return None
        peers: list[dict[str, Any]] = []
        seen: set[str] = set()
        for m in batch[0]:
            if not m:
                continue
            cid = m.get("candidate_id")
            if not cid or cid in excluded or cid in seen:
                continue
            seen.add(str(cid))
            peers.append(_peer_row_from_chroma_decision_metadata(m))
            if len(peers) >= n_results:
                break
        if not peers:
            return None
        return {"similar_decisions_same_jd": peers}
    except Exception as e:
        logger.warning("Chroma decision RAG query failed: %s", e)
        return None


def _resolve_decision_rag(
    organization_id: str,
    job_id: str,
    job_description: str,
    exclude_candidate_ids: frozenset[str] | None,
) -> dict[str, Any]:
    chroma_peers = _build_decision_rag_from_chroma(
        job_description,
        organization_id,
        job_id,
        exclude_candidate_ids=exclude_candidate_ids,
    )
    if chroma_peers is not None and chroma_peers.get("similar_decisions_same_jd"):
        return chroma_peers
    return _build_decision_rag_from_storage(
        organization_id=organization_id,
        job_id=job_id,
        exclude_candidate_ids=exclude_candidate_ids,
    )


def _status_from_score(score: float) -> str:
    """Single source of truth for the threshold rules."""
    if score >= 80:
        return "shortlist"
    if score >= 60:
        return "review"
    return "reject"


def _enforce_status_thresholds(parsed: Any) -> Any:
    """
    Overwrite status in every decision object so it always matches match_score,
    regardless of what the LLM returned. Handles both a single dict and a list.
    """
    def fix(row: Any) -> Any:
        if not isinstance(row, dict):
            return row
        score = row.get("match_score")
        try:
            score = float(score)
        except (TypeError, ValueError):
            return row
        correct = _status_from_score(score)
        if row.get("status") != correct:
            logger.warning(
                "Status mismatch corrected: LLM said %r but score %.1f → %r",
                row.get("status"), score, correct,
            )
            row["status"] = correct
        return row

    if isinstance(parsed, list):
        return [fix(item) for item in parsed]
    return fix(parsed)


def _parse_decision_json(raw_text: str) -> Any:
    """Extract first JSON value (object or array) from model output."""
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()
    if not raw_text:
        raise ValueError("LLM returned an empty response.")

    start = None
    for i, c in enumerate(raw_text):
        if c in "[{":
            start = i
            break
    if start is None:
        raise ValueError("No valid JSON found in LLM response.")

    decoder = json.JSONDecoder()
    parsed, _ = decoder.raw_decode(raw_text[start:])
    return parsed


async def run_decision_maker_agent(
    job_description: str,
    candidate_resume_assessment_json: str,
    organization_id: str,
    job_id: str,
    *,
    exclude_candidate_ids: Iterable[str] | None = None,
    rag_results: dict[str, Any] | None = None,
) -> Any:
    """
    Run the JSON decision maker with optional pre-built RAG dict.

    If *rag_results* is None, context is loaded via Chroma (then APPLICATIONS fallback).
    Returns parsed JSON (dict or list of dicts).
    """
    excluded = frozenset(exclude_candidate_ids) if exclude_candidate_ids is not None else None
    resolved_rag = rag_results or _resolve_decision_rag(
        organization_id=organization_id,
        job_id=job_id,
        job_description=job_description,
        exclude_candidate_ids=excluded,
    )
    rag_json = json.dumps(resolved_rag, indent=2)
    base_user_content = build_decision_maker_user_message(
        job_description,
        candidate_resume_assessment_json,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_PROMPT),
        ]
    )

    llm = get_chat_model()
    chain = prompt | llm

    result = await chain.ainvoke(
        {
            "base_user_content": base_user_content,
            "rag_json": rag_json,
        }
    )

    raw = result.content
    raw_text: str = raw if isinstance(raw, str) else str(raw)
    logger.debug("Decision maker raw response (first 300 chars): %.300s", raw_text)

    parsed = _parse_decision_json(raw_text)
    return _enforce_status_thresholds(parsed)


def decisions_list_from_parsed(parsed: Any) -> list[str]:
    """Normalize parsed JSON into string lines for OrchestratorState."""
    if isinstance(parsed, list):
        return [json.dumps(item, ensure_ascii=False) for item in parsed]
    return [json.dumps(parsed, ensure_ascii=False)]
