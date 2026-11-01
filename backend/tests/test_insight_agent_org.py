"""
Standalone test for InsightAgent — ORGANIZATION LEVEL.

Run from backend/:
    source venv/bin/activate
    python test_insight_agent_org.py

What this does:
  1. Builds a fake OrchestratorState with mock decisions across MULTIPLE jobs/roles
  2. Calls InsightAgent.run(state) directly — no orchestrator, no resume_analyzer
  3. Prints the insights returned by the LLM
  4. Verifies the insight was stored in ChromaDB filtered by organization_id
"""

import asyncio
import json

from app.agents.state import build_initial_state
from app.agents.sub_agents.insight_agent import InsightAgent
from app.chroma.collections import get_insights_collection


# ---------------------------------------------------------------------------
# Mock candidate decisions spanning MULTIPLE jobs (org-level view)
# ---------------------------------------------------------------------------
MOCK_DECISIONS = [
    # --- Job 1: Python Backend ---
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
        "match_score": 45.0,
        "skills_overlap_with_jd": ["Python"],
        "skills_missing_from_resume": ["Kubernetes", "Redis", "FastAPI", "PostgreSQL"],
        "status": "reject",
        "decision_reasons": ["Only basic Python", "No backend framework experience"],
        "override_status": None,
    },

    # --- Job 2: Frontend Engineer ---
    {
        "candidate_id": "cand-003",
        "job_id": "job-frontend-02",
        "role_title": "Frontend Engineer",
        "match_score": 78.0,
        "skills_overlap_with_jd": ["React", "TypeScript", "CSS"],
        "skills_missing_from_resume": ["GraphQL", "Storybook"],
        "status": "shortlist",
        "decision_reasons": ["Solid React + TS skills", "Good portfolio"],
        "override_status": None,
    },
    {
        "candidate_id": "cand-004",
        "job_id": "job-frontend-02",
        "role_title": "Frontend Engineer",
        "match_score": 55.0,
        "skills_overlap_with_jd": ["React"],
        "skills_missing_from_resume": ["TypeScript", "GraphQL", "Storybook"],
        "status": "review",
        "decision_reasons": ["React experience but no TypeScript", "Limited testing skills"],
        "override_status": None,
    },

    # --- Job 3: Data Engineer ---
    {
        "candidate_id": "cand-005",
        "job_id": "job-data-eng-03",
        "role_title": "Data Engineer",
        "match_score": 40.0,
        "skills_overlap_with_jd": ["SQL", "Python"],
        "skills_missing_from_resume": ["Spark", "Airflow", "dbt", "Snowflake"],
        "status": "reject",
        "decision_reasons": ["Basic SQL/Python only", "No pipeline or warehouse experience"],
        "override_status": None,
    },
]


async def main():
    # 1. Build state at ORGANIZATION level — no single job_id, spans all jobs
    state = build_initial_state(
        job_id=None,                        # ← None for org-level (no single job)
        candidates=[
            "cand-001", "cand-002",         # Python backend candidates
            "cand-003", "cand-004",         # Frontend candidates
            "cand-005",                     # Data engineering candidate
        ],
        organization_id="org-test-001",
        organization_name="Acme Corp",
        mode="organization_level",          # ← key change
    )

    # Inject mock decisions as if decision_maker already ran across all jobs
    state["decision_maker"]["status"] = "completed"
    state["decision_maker"]["decisions"] = MOCK_DECISIONS

    # 2. Run InsightAgent
    print("Running InsightAgent (organization level)...")
    agent = InsightAgent()
    await agent.run(state)

    # 3. Print results
    print(f"\nStatus : {state['insight_agent']['status']}")
    print("\nInsight Report:")
    print(json.dumps(state["insight_agent"]["insights"], indent=2))

    # 4. Verify ChromaDB — filter by organization_id instead of job_id
    print("\nVerifying ChromaDB storage...")
    col = get_insights_collection()
    results = col.get(
        where={"organization_id": "org-test-001"},  # ← org-level filter
        include=["metadatas"],
    )
    count = len(results["metadatas"])
    print(f"Found {count} insight record(s) in ChromaDB for org-test-001")
    if count:
        meta = results["metadatas"][0]
        print(f"  shortlist_rate    : {meta.get('shortlist_rate')}")
        print(f"  total_candidates  : {meta.get('total_candidates')}")
        print(f"  mode              : {meta.get('mode')}")
        print(f"  jobs_covered      : {meta.get('jobs_covered')}")   # org-level bonus field
        print(f"  created_at        : {meta.get('created_at')}")


if __name__ == "__main__":
    asyncio.run(main())