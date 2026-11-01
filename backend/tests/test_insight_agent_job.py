"""
Standalone test for InsightAgent.

Run from backend/:
    source venv/bin/activate
    python test_insight_agent.py

What this does:
  1. Builds a fake OrchestratorState with 4 mock candidate decisions
  2. Calls InsightAgent.run(state) directly — no orchestrator, no resume_analyzer
  3. Prints the insights returned by the LLM
  4. Verifies the insight was stored in ChromaDB insights collection
"""

import asyncio
import json

from app.agents.state import build_initial_state
from app.agents.sub_agents.insight_agent import InsightAgent
from app.chroma.collections import get_insights_collection


# ---------------------------------------------------------------------------
# Mock candidate decisions  (same shape decision_maker will produce)
# ---------------------------------------------------------------------------
MOCK_DECISIONS = [
    {
        "candidate_id": "cand-001",
        "job_id": "job-python-backend-01",
        "role_title": "Senior Python Backend Engineer",
        "match_score": 85.0,
        "skills_overlap_with_jd": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "skills_missing_from_resume": ["Kubernetes", "Redis"],
        "status": "shortlist",
        "decision_reasons": ["Strong Python and FastAPI experience", "Good system design skills"],
        "override_status": None,
    },
    {
        "candidate_id": "cand-002",
        "job_id": "job-python-backend-01",
        "role_title": "Senior Python Backend Engineer",
        "match_score": 62.0,
        "skills_overlap_with_jd": ["Python", "Django"],
        "skills_missing_from_resume": ["Kubernetes", "Redis", "FastAPI", "PostgreSQL"],
        "status": "review",
        "decision_reasons": ["Python experience but no FastAPI", "Missing cloud-native skills"],
        "override_status": None,
    },
    {
        "candidate_id": "cand-003",
        "job_id": "job-python-backend-01",
        "role_title": "Senior Python Backend Engineer",
        "match_score": 38.0,
        "skills_overlap_with_jd": ["Python"],
        "skills_missing_from_resume": ["Kubernetes", "Redis", "FastAPI", "PostgreSQL", "Docker"],
        "status": "reject",
        "decision_reasons": ["Only basic Python", "No backend framework experience"],
        "override_status": None,
    },
    {
        "candidate_id": "cand-004",
        "job_id": "job-python-backend-01",
        "role_title": "Senior Python Backend Engineer",
        "match_score": 40.0,
        "skills_overlap_with_jd": ["Python", "Flask"],
        "skills_missing_from_resume": ["Kubernetes", "Redis", "FastAPI", "PostgreSQL"],
        "status": "reject",
        "decision_reasons": ["Flask experience but not FastAPI", "No cloud experience"],
        "override_status": None,
    },
]


async def main():
    # 1. Build state directly — skipping resume_analyzer and decision_maker stages
    state = build_initial_state(
        job_id="job-python-backend-01",
        candidates=["cand-001", "cand-002", "cand-003", "cand-004"],
        organization_id="org-test-001",
        organization_name="Acme Corp",
        mode="job_level",
    )

    # Inject mock decisions as if decision_maker already ran
    state["decision_maker"]["status"] = "completed"
    state["decision_maker"]["decisions"] = MOCK_DECISIONS

    # 2. Run InsightAgent
    print("Running InsightAgent...")
    agent = InsightAgent()
    await agent.run(state)

    # 3. Print results
    print(f"\nStatus : {state['insight_agent']['status']}")
    print("\nInsight Report:")
    print(json.dumps(state["insight_agent"]["insights"], indent=2))

    # 4. Verify it was stored in ChromaDB
    print("\nVerifying ChromaDB storage...")
    col = get_insights_collection()
    results = col.get(
        where={"job_id": "job-python-backend-01"},
        include=["metadatas"],
    )
    count = len(results["metadatas"])
    print(f"Found {count} insight record(s) in ChromaDB for job-python-backend-01")
    if count:
        meta = results["metadatas"][0]
        print(f"  shortlist_rate    : {meta['shortlist_rate']}")
        print(f"  total_candidates  : {meta['total_candidates']}")
        print(f"  mode              : {meta['mode']}")
        print(f"  created_at        : {meta['created_at']}")


if __name__ == "__main__":
    asyncio.run(main())
