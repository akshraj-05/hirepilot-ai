"use client";

import { useEffect, useMemo, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { JobsTable } from "@/components/jobs/JobsTable";
import { listJobs, updateJobStatus } from "@/utils/api";
import type { JobPosting, JobPostingStatus } from "@/utils/types";
import { printJobsReport, printAllJobsInsightsReport } from "@/utils/reportPdf";

function parseJobStatusFilter(value: string): JobPostingStatus | "all" {
  if (
    value === "open" ||
    value === "closed" ||
    value === "draft" ||
    value === "paused"
  ) {
    return value;
  }
  return "all";
}

/** Jobs posted by HR: fetched from backend, with search and status filter. */
export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  useEffect(() => {
    listJobs()
      .then((data) => {
        const mapped: JobPosting[] = data.map((j) => ({
          id: j.job_id,
          jobId: j.job_id,
          role: j.title || j.job_id,
          description: j.job_description,
          datePosted: j.date_posted || new Date().toISOString().slice(0, 10),
          status: (j.status as JobPostingStatus) || "draft",
        }));
        setJobs(mapped);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleStatusChange = async (jobId: string, newStatus: string) => {
    try {
      await updateJobStatus(jobId, newStatus);
      setJobs((prev) =>
        prev.map((j) =>
          j.id === jobId ? { ...j, status: newStatus as JobPostingStatus } : j
        )
      );
    } catch {
      // status update failed silently; table stays unchanged
    }
  };

  const filtered = useMemo(() => {
    const st = parseJobStatusFilter(statusFilter);
    const q = search.trim().toLowerCase();
    return jobs.filter((job) => {
      if (st !== "all" && job.status !== st) return false;
      if (q) {
        const hay = `${job.jobId} ${job.role} ${job.description}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [jobs, statusFilter, search]);

  const inputClass =
    "rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:border-[var(--hp-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]/20";

  return (
    <>
      <TopBar
        title="Job postings"
        subtitle="All roles published by your HR team."
        actions={
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={jobs.length === 0}
              onClick={() => printAllJobsInsightsReport(jobs)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-4 py-2 text-sm font-medium text-[var(--hp-text)] hover:bg-[var(--hp-surface)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ↓ Comprehensive Job Report
            </button>
            <button
              type="button"
              disabled={filtered.length === 0}
              onClick={() => printJobsReport(filtered, "Current View Report")}
              className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--hp-accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ↓ Job Report
            </button>
          </div>
        }
      />

      <div className="mb-4 flex flex-col gap-4">
        <div className="w-full max-w-md">
          <label
            htmlFor="job-search"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Search
          </label>
          <input
            id="job-search"
            type="search"
            placeholder="Search by job ID, role, or description…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`w-full ${inputClass}`}
            autoComplete="off"
          />
        </div>

        <div>
          <label
            htmlFor="job-status-filter"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Status
          </label>
          <select
            id="job-status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={inputClass}
          >
            <option value="all">All</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="draft">Draft</option>
            <option value="paused">Paused</option>
          </select>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-[var(--hp-text-muted)]">Loading jobs…</p>
      ) : jobs.length === 0 ? (
        <p className="text-sm text-[var(--hp-text-muted)]">
          No jobs yet. Go to Upload to create one.
        </p>
      ) : (
        <JobsTable rows={filtered} onStatusChange={handleStatusChange} />
      )}
    </>
  );
}
