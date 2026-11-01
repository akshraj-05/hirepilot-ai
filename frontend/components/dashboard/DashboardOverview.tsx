"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { JobStatusSummaryCards } from "@/components/dashboard/JobStatusSummaryCards";
import { HiringFunnel } from "@/components/dashboard/HiringFunnel";
import { AIInsightsPanel } from "@/components/dashboard/AIInsightsPanel";
import { getDashboardStats, getAIInsights, getRecentActivity, listCandidates, listJobs, type AIInsight } from "@/utils/api";

const CandidateDistributionCharts = dynamic(
  () =>
    import("@/components/dashboard/CandidateDistributionCharts").then((m) => ({
      default: m.CandidateDistributionCharts,
    })),
  {
    ssr: false,
    loading: () => (
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-[280px] animate-pulse rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface)]" />
        <div className="h-[280px] animate-pulse rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface)]" />
      </div>
    ),
  },
);

type StatsRow = {
  total: number;
  shortlisted: number;
  rejected: number;
  review: number;
};

const ZERO_STATS: StatsRow = { total: 0, shortlisted: 0, rejected: 0, review: 0 };

/** Dashboard: pipeline overview using live backend data. */
export function DashboardOverview() {
  const [jobs, setJobs] = useState<{ job_id: string; title: string }[]>([]);
  const [jobFilter, setJobFilter] = useState<string>("all");
  const [stats, setStats] = useState<StatsRow>(ZERO_STATS);
  const [candidates, setCandidates] = useState<
    { id: string; name: string; score: number; status: string; jobId: string }[]
  >([]);
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [activity, setActivity] = useState<{ id: string; message: string; time_label: string; status: string }[]>([]);

  // Load jobs once
  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => {});
    getRecentActivity().then(setActivity).catch(() => {});
  }, []);

  // Load stats, candidates, and insights when job filter changes
  useEffect(() => {
    if (jobs.length === 0) return;

    const fetchData = async () => {
      if (jobFilter === "all") {
        // Sum stats across all jobs
        const results = await Promise.all(
          jobs.map((j) => getDashboardStats(j.job_id).catch(() => ZERO_STATS))
        );
        const combined = results.reduce<StatsRow>(
          (acc, r) => ({
            total: acc.total + r.total,
            shortlisted: acc.shortlisted + r.shortlisted,
            rejected: acc.rejected + r.rejected,
            review: acc.review + r.review,
          }),
          { ...ZERO_STATS }
        );
        setStats(combined);

        const cRows = await Promise.all(
          jobs.map((j) =>
            listCandidates(j.job_id)
              .then((rows) => rows.map((c) => ({ ...c, jobId: j.job_id })))
              .catch(() => [] as { id: string; name: string; score: number; status: string; jobId: string }[])
          )
        );
        setCandidates(cRows.flat());

        // Org-wide insights (no job_id)
        const ins = await getAIInsights().catch(() => [] as AIInsight[]);
        setInsights(ins);
      } else {
        const s = await getDashboardStats(jobFilter).catch(() => ZERO_STATS);
        setStats(s);

        const rows = await listCandidates(jobFilter).catch(() => []);
        setCandidates(rows.map((c) => ({ ...c, jobId: jobFilter })));

        // Job-specific insights
        const ins = await getAIInsights(jobFilter).catch(() => [] as AIInsight[]);
        setInsights(ins);
      }
    };

    fetchData();
  }, [jobFilter, jobs]);

  const funnelStats = useMemo(
    () => ({
      total: stats.total,
      shortlist: stats.shortlisted,
      reject: stats.rejected,
      review: stats.review,
    }),
    [stats]
  );

  const jobStatusCounts = useMemo(
    () => ({ open: jobs.length, closed: 0, draft: 0, paused: 0 }),
    [jobs]
  );

  const chartCandidates = useMemo(
    () =>
      candidates.map((c) => ({
        id: c.id,
        name: c.name,
        matchScore: c.score,
        status: c.status.toLowerCase() as "shortlist" | "review" | "reject",
        jobId: c.jobId,
        postedJobId: c.jobId,
        title: "",
        yearsExperience: 0,
        email: "",
        experienceSummary: "",
        skills: [] as string[],
        decisionReasons: [] as string[],
        skillsOverlapWithJD: [] as string[],
        skillsMissingFromResume: [] as string[],
      })),
    [candidates]
  );

  const selectClass =
    "mt-1 w-full max-w-md rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:border-[var(--hp-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]/20";

  return (
    <>
      <TopBar
        title="Dashboard"
        subtitle="Pipeline overview and AI-derived signals."
      />

      {/* Job filter */}
      <div className="mb-6">
        <label
          htmlFor="dashboard-job-filter"
          className="text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
        >
          Filter by job
        </label>
        <select
          id="dashboard-job-filter"
          value={jobFilter}
          onChange={(e) => setJobFilter(e.target.value)}
          className={selectClass}
        >
          <option value="all">All jobs</option>
          {jobs.map((j) => (
            <option key={j.job_id} value={j.job_id}>
              {j.title || j.job_id}
            </option>
          ))}
        </select>
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-[var(--hp-text)]">
          Job postings by status
        </h2>
        <JobStatusSummaryCards counts={jobStatusCounts} />
      </section>

      <section className="mt-8 space-y-4">
        <HiringFunnel stats={funnelStats} />
      </section>

      <section className="mt-8">
        <CandidateDistributionCharts candidates={chartCandidates} />
      </section>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(380px,34rem)_1fr] lg:items-start">
        <div className="flex min-h-0 flex-col gap-4">
          <AIInsightsPanel
            insights={insights}
            stats={stats}
            candidateCount={stats.total}
          />
          <div className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] p-5 shadow-[var(--hp-shadow)]">
            <h2 className="text-sm font-semibold text-[var(--hp-text)]">
              Quick actions
            </h2>
            <p className="mt-1 text-sm text-[var(--hp-text-muted)]">
              Upload a resume and run AI analysis against a job.
            </p>
            <Link
              href="/upload"
              className="mt-4 inline-flex w-full items-center justify-center rounded-lg bg-[var(--hp-accent)] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700"
            >
              Upload resume
            </Link>
          </div>
        </div>
        <div className="min-w-0 self-start">
          <RecentActivity
            items={activity.map((a) => ({
              id: a.id,
              message: a.message,
              timeLabel: a.time_label,
              status: a.status as "shortlist" | "review" | "reject",
            }))}
          />
        </div>
      </div>
    </>
  );
}
