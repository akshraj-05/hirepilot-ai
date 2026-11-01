"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { JobPosting, JobPostingStatus } from "@/utils/types";
import { JobStatusBadge } from "@/components/ui/JobStatusBadge";

const STATUS_SELECT_STYLES: Record<JobPostingStatus, string> = {
  open: "bg-[var(--hp-shortlist-bg)] text-[var(--hp-shortlist)] ring-green-600/20",
  closed: "bg-[var(--hp-surface)] text-[var(--hp-text-muted)] ring-[var(--hp-border)]",
  draft: "bg-[var(--hp-review-bg)] text-[var(--hp-review)] ring-yellow-600/20",
  paused: "bg-orange-100 text-orange-700 ring-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:ring-orange-700/40",
};

export type JobSortKey =
  | "jobId"
  | "role"
  | "description"
  | "datePosted"
  | "status";

export type JobSortDir = "asc" | "desc";

const JOB_STATUSES: JobPostingStatus[] = ["open", "closed", "draft", "paused"];

type JobsTableProps = {
  rows: JobPosting[];
  className?: string;
  onStatusChange?: (jobId: string, newStatus: string) => Promise<void>;
};

/**
 * Sortable jobs table: Job ID, role, description preview, date posted, status.
 */
export function JobsTable({ rows, className = "", onStatusChange }: JobsTableProps) {
  const [sortKey, setSortKey] = useState<JobSortKey>("datePosted");
  const [sortDir, setSortDir] = useState<JobSortDir>("desc");
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "jobId") {
        cmp = a.jobId.localeCompare(b.jobId, undefined, { numeric: true });
      } else if (sortKey === "role") {
        cmp = a.role.localeCompare(b.role);
      } else if (sortKey === "description") {
        cmp = a.description.localeCompare(b.description);
      } else if (sortKey === "datePosted") {
        cmp = a.datePosted.localeCompare(b.datePosted);
      } else {
        cmp = a.status.localeCompare(b.status);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const toggleSort = (key: JobSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(
        key === "role" || key === "jobId" || key === "description"
          ? "asc"
          : "desc",
      );
    }
  };

  const headerBtn = (key: JobSortKey, label: string) => (
    <button
      type="button"
      onClick={() => toggleSort(key)}
      className="flex items-center gap-1 font-semibold text-[var(--hp-text)] hover:text-[var(--hp-accent)]"
    >
      {label}
      {sortKey === key && (
        <span className="text-xs text-[var(--hp-text-muted)]">
          {sortDir === "asc" ? "↑" : "↓"}
        </span>
      )}
    </button>
  );

  const formatPosted = (iso: string) => {
    try {
      return new Intl.DateTimeFormat("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      }).format(new Date(iso + "T12:00:00"));
    } catch {
      return iso;
    }
  };

  return (
    <div
      className={`overflow-x-auto rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] shadow-[var(--hp-shadow)] ${className}`}
    >
      <table className="min-w-[720px] w-full text-left text-sm">
        <thead className="border-b border-[var(--hp-border)] bg-[var(--hp-surface)]">
          <tr>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("jobId", "Job ID")}
            </th>
            <th className="min-w-[140px] px-4 py-3">
              {headerBtn("role", "Job role")}
            </th>
            <th className="min-w-[220px] px-4 py-3">
              {headerBtn("description", "Job description")}
            </th>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("datePosted", "Date posted")}
            </th>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("status", "Status")}
            </th>
            <th className="whitespace-nowrap px-4 py-3 text-right text-[var(--hp-text-muted)] font-semibold">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--hp-border)]">
          {sorted.length === 0 ? (
            <tr>
              <td
                colSpan={6}
                className="px-4 py-10 text-center text-sm text-[var(--hp-text-muted)]"
              >
                No jobs match your filters or search.
              </td>
            </tr>
          ) : (
            sorted.map((row) => (
              <tr
                key={row.id}
                className="transition-colors hover:bg-[var(--hp-surface)] align-top"
              >
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs font-medium text-[var(--hp-text)]">
                  {row.jobId}
                </td>
                <td className="px-4 py-3 font-medium text-[var(--hp-text)]">
                  {row.role}
                </td>
                <td className="max-w-md px-4 py-3 text-[var(--hp-text-muted)]">
                  <p className="line-clamp-2" title={row.description}>
                    {row.description}
                  </p>
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums text-[var(--hp-text)]">
                  {formatPosted(row.datePosted)}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  {onStatusChange ? (
                    <select
                      disabled={updatingId === row.id}
                      value={row.status}
                      onChange={async (e) => {
                        setUpdatingId(row.id);
                        await onStatusChange(row.id, e.target.value);
                        setUpdatingId(null);
                      }}
                      className={`cursor-pointer rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)] disabled:cursor-not-allowed disabled:opacity-50 transition-colors ${STATUS_SELECT_STYLES[row.status]}`}
                    >
                      {JOB_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s.charAt(0).toUpperCase() + s.slice(1)}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <JobStatusBadge status={row.status} />
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right">
                  <Link
                    href={`/jobs/${row.jobId}/insights`}
                    className="text-sm font-medium text-[var(--hp-accent)] hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
