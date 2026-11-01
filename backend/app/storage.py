"""In-memory stores for candidates, jobs, applications, and feedback."""

from typing import Any

# candidate_id -> record (may include resume_content bytes — strip before JSON)
CANDIDATES: dict[str, dict[str, Any]] = {}

# job_id -> { title, description, organization_id }
JOBS: dict[str, dict[str, Any]] = {}

# (organization_id, job_id, candidate_id) -> application / analysis state
APPLICATIONS: dict[tuple[str, str, str], dict[str, Any]] = {}

FEEDBACK: list[dict[str, Any]] = []

_PRIVATE = frozenset({"resume_content"})


def public_candidate(record: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in _PRIVATE}


def application_key(organization_id: str, job_id: str, candidate_id: str) -> tuple[str, str, str]:
    return (organization_id, job_id, candidate_id)
