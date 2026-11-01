"use client";

import { useEffect, useMemo, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { MeetingsTable } from "@/components/meetings/MeetingsTable";
import { ScheduleMeetingModal } from "@/components/meetings/ScheduleMeetingModal";
import { listMeetings, listJobs, listCandidates } from "@/utils/api";
import type { Meeting, MeetingStatus, MeetingType } from "@/utils/types";

const inputClass =
  "rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:border-[var(--hp-accent)] focus:outline-none focus:ring-2 focus:ring-[var(--hp-accent)]/20";

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  const [candidates, setCandidates] = useState<{ id: string; name: string; jobId: string }[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<string>("");

  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [search, setSearch] = useState<string>("");

  async function fetchMeetings() {
    try {
      const data = await listMeetings();
      setMeetings(data as Meeting[]);
    } catch {
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMeetings();
    listJobs()
      .then(async (jobList) => {
        const all = await Promise.all(
          jobList.map((j) =>
            listCandidates(j.job_id)
              .then((rows) => rows.map((c) => ({ ...c, jobId: j.job_id })))
              .catch(() => [])
          )
        );
        const seen = new Set<string>();
        setCandidates(
          all.flat().filter((c) => {
            if (seen.has(c.id)) return false;
            seen.add(c.id);
            return true;
          })
        );
      })
      .catch(() => {});
  }, []);

  const scheduledCandidateIds = useMemo(
    () => new Set(meetings.map((m) => m.candidate_id)),
    [meetings]
  );

  const selected = candidates.find((c) => c.id === selectedCandidate);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    return meetings.filter((m) => {
      if (typeFilter !== "all" && m.meeting_type !== typeFilter) return false;
      if (statusFilter !== "all" && m.status !== statusFilter) return false;

      if (dateFrom) {
        const mDate = m.scheduled_at.slice(0, 10);
        if (mDate < dateFrom) return false;
      }
      if (dateTo) {
        const mDate = m.scheduled_at.slice(0, 10);
        if (mDate > dateTo) return false;
      }

      if (q) {
        const hay =
          `${m.title} ${m.interviewer_name} ${m.interviewer_email} ${m.posted_job_id} ${m.notes ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }

      return true;
    });
  }, [meetings, typeFilter, statusFilter, dateFrom, dateTo, search]);

  return (
    <>
      <TopBar
        title="Scheduled meetings"
        subtitle="All interviews and calls — filter, search, and sort."
      />

      <div className="mb-4 flex flex-col gap-4">
        {/* Quick-schedule row */}
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
              Candidate
            </label>
            <select
              value={selectedCandidate}
              onChange={(e) => setSelectedCandidate(e.target.value)}
              className={inputClass}
            >
              <option value="">Select candidate</option>
              {candidates.map((c) => (
                <option key={c.id} value={c.id} disabled={scheduledCandidateIds.has(c.id)}>
                  {c.name}{scheduledCandidateIds.has(c.id) ? " (scheduled)" : ""}
                </option>
              ))}
            </select>
          </div>
          <ScheduleMeetingModal
            candidateId={selected?.id}
            candidateName={selected?.name}
            jobId={selected?.jobId}
            disabled={!selected || scheduledCandidateIds.has(selected.id)}
            onCreated={fetchMeetings}
          />
        </div>

        {/* Search */}
        <div className="w-full max-w-md">
          <label
            htmlFor="meeting-search"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Search
          </label>
          <input
            id="meeting-search"
            type="search"
            placeholder="Search by title, interviewer, job, notes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={`w-full ${inputClass}`}
            autoComplete="off"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <div>
            <label
              htmlFor="meeting-type"
              className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
            >
              Type
            </label>
            <select
              id="meeting-type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as MeetingType | "all")}
              className={inputClass}
            >
              <option value="all">All types</option>
              <option value="phone_screen">Phone screen</option>
              <option value="technical">Technical</option>
              <option value="hr_round">HR round</option>
              <option value="final">Final</option>
              <option value="offer">Offer</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="meeting-status"
              className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
            >
              Status
            </label>
            <select
              id="meeting-status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as MeetingStatus | "all")}
              className={inputClass}
            >
              <option value="all">All statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="rescheduled">Rescheduled</option>
            </select>
          </div>

          <div>
            <label
              htmlFor="meeting-date-from"
              className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
            >
              From
            </label>
            <input
              id="meeting-date-from"
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label
              htmlFor="meeting-date-to"
              className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
            >
              To
            </label>
            <input
              id="meeting-date-to"
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-[var(--hp-text-muted)]">Loading meetings…</p>
      ) : (
        <MeetingsTable rows={filtered} />
      )}
    </>
  );
}
