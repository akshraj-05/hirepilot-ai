"use client";

import { useMemo, useState } from "react";
import type { Meeting, MeetingStatus, MeetingType } from "@/utils/types";

export type MeetingSortKey =
  | "title"
  | "meeting_type"
  | "status"
  | "scheduled_at"
  | "duration_mins"
  | "interviewer_name";

type MeetingsTableProps = {
  rows: Meeting[];
  className?: string;
};

const statusStyles: Record<MeetingStatus, string> = {
  scheduled:
    "bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]",
  completed:
    "bg-[var(--hp-shortlist-bg)] text-[var(--hp-shortlist)]",
  cancelled:
    "bg-[var(--hp-reject-bg)] text-[var(--hp-reject)]",
  rescheduled:
    "bg-[var(--hp-review-bg)] text-[var(--hp-review)]",
};

const typeLabels: Record<MeetingType, string> = {
  phone_screen: "Phone screen",
  technical: "Technical",
  hr_round: "HR round",
  final: "Final",
  offer: "Offer",
};

function formatDateTime(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function shortenId(id: string): string {
  return id.length > 8 ? id.slice(0, 8) + "…" : id;
}

/**
 * Sortable meetings table: title, candidate, job, type, status, scheduled at, duration, interviewer.
 */
export function MeetingsTable({ rows, className = "" }: MeetingsTableProps) {
  const [sortKey, setSortKey] = useState<MeetingSortKey>("scheduled_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      let cmp = 0;
      if (sortKey === "scheduled_at") {
        cmp = a.scheduled_at.localeCompare(b.scheduled_at);
      } else if (sortKey === "duration_mins") {
        cmp = a.duration_mins - b.duration_mins;
      } else {
        cmp = (a[sortKey] as string).localeCompare(b[sortKey] as string);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const toggleSort = (key: MeetingSortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "scheduled_at" ? "asc" : "asc");
    }
  };

  const headerBtn = (key: MeetingSortKey, label: string) => (
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
      <table className="min-w-[900px] w-full text-left text-sm">
        <thead className="border-b border-[var(--hp-border)] bg-[var(--hp-surface)]">
          <tr>
            <th className="min-w-[180px] px-4 py-3">
              {headerBtn("title", "Title")}
            </th>
            <th className="min-w-[130px] px-4 py-3 font-semibold text-[var(--hp-text)]">
              Candidate
            </th>
            <th className="whitespace-nowrap px-4 py-3 font-semibold text-[var(--hp-text)]">
              Job
            </th>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("status", "Status")}
            </th>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("scheduled_at", "Scheduled at")}
            </th>
            <th className="whitespace-nowrap px-4 py-3">
              {headerBtn("duration_mins", "Duration")}
            </th>
            <th className="min-w-[130px] px-4 py-3">
              {headerBtn("interviewer_name", "Interviewer")}
            </th>
            <th className="whitespace-nowrap px-4 py-3 font-semibold text-[var(--hp-text)]">
              Link / Location
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--hp-border)]">
          {sorted.length === 0 ? (
            <tr>
              <td
                colSpan={9}
                className="px-4 py-10 text-center text-sm text-[var(--hp-text-muted)]"
              >
                No meetings match your filters.
              </td>
            </tr>
          ) : (
            sorted.map((row) => (
              <tr
                key={row.id}
                className="align-top transition-colors hover:bg-[var(--hp-surface)]"
              >
                <td className="px-4 py-3 font-medium text-[var(--hp-text)]">
                  {row.title}
                </td>
                <td className="px-4 py-3 text-[var(--hp-text)]">
                  {shortenId(row.candidate_id)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-[var(--hp-text-muted)]">
                  {row.posted_job_id}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-[var(--hp-text-muted)]">
                  {typeLabels[row.meeting_type]}
                </td>
                <td className="whitespace-nowrap px-4 py-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${statusStyles[row.status]}`}
                  >
                    {row.status}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums text-[var(--hp-text)]">
                  {formatDateTime(row.scheduled_at)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 tabular-nums text-[var(--hp-text-muted)]">
                  {row.duration_mins} min
                </td>
                <td className="px-4 py-3 text-[var(--hp-text)]">
                  <div>{row.interviewer_name}</div>
                  <div className="text-xs text-[var(--hp-text-muted)]">
                    {row.interviewer_email}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm">
                  {row.meeting_link ? (
                    <a
                      href={row.meeting_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[var(--hp-accent)] hover:underline"
                    >
                      Join link
                    </a>
                  ) : row.location ? (
                    <span className="text-[var(--hp-text-muted)]">
                      {row.location}
                    </span>
                  ) : (
                    <span className="text-[var(--hp-text-muted)]">—</span>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
