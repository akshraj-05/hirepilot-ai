/**
 * Pure helpers for dashboard aggregates. Safe to keep; they operate on data passed in.
 * TODO(mock-removal): Callers should pass API-fetched rows instead of mockCandidates/mockJobPostings.
 */
import type { Candidate, JobPosting } from "./types";

/** Filter dashboard metrics to one posting or the full pipeline */
export function filterCandidatesByJobId(
  candidates: Candidate[],
  jobId: string | "all",
): Candidate[] {
  if (jobId === "all") return candidates;
  return candidates.filter((c) => c.postedJobId === jobId);
}

/** Counts for hiring funnel stages (statuses partition the set) */
export function getFunnelStats(candidates: Candidate[]) {
  const total = candidates.length;
  const shortlist = candidates.filter((c) => c.status === "shortlist").length;
  const review = candidates.filter((c) => c.status === "review").length;
  const reject = candidates.filter((c) => c.status === "reject").length;
  return { total, shortlist, review, reject };
}

/** Pie / legend data: shortlisted vs rejected vs review */
export function getStatusDistribution(candidates: Candidate[]) {
  const { shortlist, review, reject } = getFunnelStats(candidates);
  return [
    { name: "Shortlisted", value: shortlist, key: "shortlist" as const },
    { name: "In review", value: review, key: "review" as const },
    { name: "Rejected", value: reject, key: "reject" as const },
  ];
}

/**
 * Histogram buckets aligned with product spec:
 * 0–50, 50–70, 70–90+, treating 90+ as part of the top bucket.
 */
export function getScoreRangeBuckets(candidates: Candidate[]) {
  let low = 0;
  let mid = 0;
  let high = 0;
  for (const c of candidates) {
    const s = c.matchScore;
    if (s <= 50) low++;
    else if (s <= 70) mid++;
    else high++;
  }
  return [
    { range: "0 – 50", count: low },
    { range: "50 – 70", count: mid },
    { range: "70 – 100", count: high },
  ];
}

/** HR job board status totals (independent of candidate job filter) */
export function getJobPostingStatusCounts(jobs: JobPosting[]) {
  const counts = { open: 0, closed: 0, draft: 0, paused: 0 };
  for (const j of jobs) {
    counts[j.status]++;
  }
  return counts;
}

/** Most common JD gaps from AI-extracted missing skills */
export function getTopMissingSkills(candidates: Candidate[], limit = 5) {
  const map = new Map<string, number>();
  for (const c of candidates) {
    for (const skill of c.skillsMissingFromResume) {
      map.set(skill, (map.get(skill) ?? 0) + 1);
    }
  }
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([skill, count]) => ({ skill, count }));
}
