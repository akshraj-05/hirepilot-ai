"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { Candidate, CandidateStatus } from "@/utils/types";
import { Badge } from "./Badge";

export type SortKey = "name" | "matchScore" | "status";
export type SortDir = "asc" | "desc";

type DataTableProps = {
  rows: Candidate[];
  className?: string;
};

/**
 * Sortable candidate table with link to detail rows.
 */
export function DataTable({ rows, className = "" }: DataTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("matchScore");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "name") {
        cmp = a.name.localeCompare(b.name);
      } else if (sortKey === "matchScore") {
        cmp = a.matchScore - b.matchScore;
      } else {
        cmp = a.status.localeCompare(b.status);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "name" ? "asc" : "desc");
    }
  };

  const headerBtn = (key: SortKey, label: string) => (
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

  return (
    <div
      className={`overflow-x-auto rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] shadow-[var(--hp-shadow)] ${className}`}
    >
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-[var(--hp-border)] bg-[var(--hp-surface)]">
          <tr>
            <th className="px-4 py-3">{headerBtn("name", "Name")}</th>
            <th className="px-4 py-3">{headerBtn("matchScore", "Match score")}</th>
            <th className="px-4 py-3">{headerBtn("status", "Status")}</th>
            <th className="px-4 py-3 font-semibold text-[var(--hp-text)]">Source</th>
            <th className="px-4 py-3 font-semibold text-[var(--hp-text)]">Phone number</th>
            <th className="px-4 py-3 w-96 font-semibold text-[var(--hp-text)]">Summary</th>
            <th className="px-4 py-3 text-right text-[var(--hp-text-muted)]">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--hp-border)]">
          {sorted.map((row) => (
            <tr
              key={row.id}
              className="hover:bg-[var(--hp-surface)] transition-colors"
            >
              <td className="px-4 py-3">
                <Link
                  href={`/candidates/${row.id}${row.postedJobId ? `?job_id=${row.postedJobId}` : ""}`}
                  className="font-medium text-[var(--hp-text)] hover:text-[var(--hp-accent)] hover:underline"
                >
                  {row.name}
                </Link>
                <div className="text-xs text-[var(--hp-text-muted)]">
                  {row.title}
                </div>
              </td>
              <td className="px-4 py-3 tabular-nums font-medium">
                {row.matchScore}%
              </td>
              <td className="px-4 py-3">
                <Badge status={row.status} />
              </td>
              <td className="px-4 py-3 text-sm">
                <span className="inline-block rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                  {row.source_platform ? (
                    row.source_platform.charAt(0).toUpperCase() + row.source_platform.slice(1)
                  ) : (
                    "Manual"
                  )}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-[var(--hp-text-muted)]">
                {row.phone || "—"}
              </td>
              <td className="px-4 py-4 w-96">
                <p className="text-sm leading-relaxed text-[var(--hp-text-muted)] line-clamp-3">
                  {row.experienceSummary || "—"}
                </p>
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/candidates/${row.id}${row.postedJobId ? `?job_id=${row.postedJobId}` : ""}`}
                  className="text-sm font-medium text-[var(--hp-accent)] hover:underline"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Map filter UI values to CandidateStatus */
export function parseStatusFilter(
  value: string,
): CandidateStatus | "all" {
  if (value === "shortlist" || value === "reject" || value === "review") {
    return value;
  }
  return "all";
}
