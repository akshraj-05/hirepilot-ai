"""Resume Analyzer sub-agent — mutates state["resume_analyzer"] in place."""

import json
import logging
import re
import uuid

from langchain_core.prompts import PromptTemplate

from app.agents.llm import get_agent_llm
from app.agents.state import OrchestratorState
from app.agents.prompt.resume_analyzer_prompt import RESUME_ANALYZER_PROMPT
from app.db.engine import AsyncSessionLocal
from app.db.crud import uploaded_resumes, candidates

log = logging.getLogger(__name__)


def _extract_json(text: str) -> str:
    """Strip markdown fences or surrounding prose and return the raw JSON string."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return match.group(0).strip()
    return text.strip()


def _parse_json_lenient(raw: str) -> dict:
    """Try json.loads first; on failure fix common LLM quirks and retry."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fixed = re.sub(r",\s*([}\]])", r"\1", raw)
        fixed = fixed.replace("'", '"')
        return json.loads(fixed)

def _ensure_list(val) -> list:
    """Ensure flags are always a list, never a dict or string."""
    if isinstance(val, list):
        # If it's a list of dicts, convert each to string representation
        if val and isinstance(val[0], dict):
            return [str(item) for item in val if item]
        # If it's already a list of strings, return as-is
        if val and isinstance(val[0], str):
            return val
        return [str(item) for item in val if item]
    if isinstance(val, dict):
        # Handle case where dict has string keys and values
        result = []
        for k, v in val.items():
            if isinstance(v, list):
                result.extend([str(item) for item in v])
            else:
                result.append(str(v))
        return result
    if isinstance(val, str):
        val = val.strip()
        # Try to parse as JSON array first
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                return _ensure_list(parsed)
            except json.JSONDecodeError:
                pass
        # Try to parse as JSON object
        if val.startswith("{") and val.endswith("}"):
            try:
                parsed = json.loads(val)
                return _ensure_list(parsed)
            except json.JSONDecodeError:
                # If it's malformed JSON, try to extract strings between quotes
                import re
                matches = re.findall(r'"([^"]*)"', val)
                if matches:
                    return matches
        # If it's not JSON, return as single-item list
        return [val] if val else []
    return []


class ResumeAnalyzer:
    def __init__(self):
        self.chain = PromptTemplate.from_template(RESUME_ANALYZER_PROMPT) | get_agent_llm()

    async def _cleanup_candidate(self, cid: uuid.UUID) -> None:
        """Remove candidate and their uploaded resumes on analysis failure."""
        try:
            async with AsyncSessionLocal() as db:
                await uploaded_resumes.delete_by_candidate(db, cid)
                await candidates.delete(db, cid)
            log.info("Cleaned up candidate %s and their resumes after analysis failure", cid)
        except Exception:
            log.exception("Failed to clean up candidate %s", cid)

    async def run(self, state: OrchestratorState) -> None:
        state["resume_analyzer"]["status"] = "inprogress"

        try:
            candidate_uuids = [uuid.UUID(cid) for cid in state["candidates"]]

            async with AsyncSessionLocal() as db:
                resume_map = await uploaded_resumes.get_parsed_text_by_candidates(db, candidate_uuids)

                if not resume_map:
                    raise RuntimeError("No parsed resume text found in DB for the given candidates.")

                for cid_uuid in candidate_uuids:
                    resume_text = resume_map.get(cid_uuid)
                    if not resume_text:
                        continue

                    parsed = None
                    for attempt in range(3):
                        result = await self.chain.ainvoke({"resume_text": resume_text})
                        raw = _extract_json(result.content)
                        try:
                            parsed = _parse_json_lenient(raw)
                            break
                        except json.JSONDecodeError:
                            log.warning(
                                "JSON parse failed for candidate %s (attempt %d/3)",
                                cid_uuid, attempt + 1,
                            )
                    if parsed is None:
                        raise RuntimeError(
                            f"Failed to parse LLM JSON for candidate {cid_uuid} after 3 attempts"
                        )

                    yrs = parsed.get("years_experience")
                    if yrs is not None:
                        yrs = int(yrs)

                    email = parsed.get("email")
                    if not email:
                        raise RuntimeError(
                            f"Resume for candidate {cid_uuid} does not contain an email address."
                        )

                    fields = dict(
                        name=parsed.get("name"),
                        email=email,
                        mobile_number=parsed.get("mobile_number"),
                        title=parsed.get("title"),
                        years_experience=yrs,
                        experience_summary=parsed.get("experience_summary"),
                        project_summary=parsed.get("project_summary"),
                        work_summary=parsed.get("work_summary"),
                        skills=parsed.get("skills"),
                        red_flags=_ensure_list(parsed.get("red_flags")),
                        green_flags=_ensure_list(parsed.get("green_flags")),
                    )

                    target_id = cid_uuid

                    existing = await candidates.get_by_email(db, uuid.UUID(state["organization_id"]), email)
                    if existing and existing.id != cid_uuid:
                        target_id = existing.id
                        await uploaded_resumes.delete_by_candidate(db, cid_uuid)
                        await candidates.delete(db, cid_uuid)
                        state["candidates"] = [str(existing.id)]

                    await candidates.update(db, target_id, **fields)

                    state["resume_analyzer"]["analyzed_candidates"].append(raw)

            state["resume_analyzer"]["status"] = "completed"

        except Exception as e:
            state["resume_analyzer"]["status"] = "failed"
            state["resume_analyzer"]["analyzed_candidates"] = []
            for cid in candidate_uuids:
                await self._cleanup_candidate(cid)
            raise RuntimeError(f"ResumeAnalyzer failed: {e}") from e
