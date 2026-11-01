"use client";

import { useEffect, useMemo, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { DataTable, parseStatusFilter } from "@/components/ui/DataTable";
import {
  listCandidates,
  listJobs,
  listMeetings,
  listInvitedCandidates,
  createAvailabilityInvite,
  sendSchedulingEmail,
  getGoogleAuthStatus,
  getGoogleAuthUrl,
  syncNaukriCandidates,
} from "@/utils/api";

type Candidate = {
  id: string;
  name: string;
  score: number;
  status: string;
  jobId: string;
  phone_number: string;
  summary: string;
  source_platform?: string;
};

export default function CandidatesPage() {
  const [jobs, setJobs] = useState<{ job_id: string; title: string }[]>([]);
  const [selectedJob, setSelectedJob] = useState<string>("all");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [minScore, setMinScore] = useState<string>("");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  const [confirmedIds, setConfirmedIds] = useState<Set<string>>(new Set());
  const [inviteTokens, setInviteTokens] = useState<Map<string, string>>(new Map());
  const [scheduling, setScheduling] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null);

  useEffect(() => {
    listJobs()
      .then((data) => setJobs(data))
      .catch(() => {});

    getGoogleAuthStatus()
      .then((s) => setGoogleConnected(s.connected))
      .catch(() => setGoogleConnected(false));

    Promise.all([
      listMeetings().catch(() => []),
      listInvitedCandidates().catch(() => ({ invites: [] })),
    ]).then(([meetings, invited]) => {
      const done = new Set<string>();
      const tokens = new Map<string, string>();

      for (const m of meetings) done.add(m.candidate_id);
      for (const inv of invited.invites) {
        done.add(inv.candidate_id);
        tokens.set(inv.candidate_id, inv.token);
      }
      setConfirmedIds(done);
      setInviteTokens(tokens);
    });
  }, []);

  useEffect(() => {
    if (jobs.length === 0) return;
    setLoading(true);

    const fetchAll = async () => {
      if (selectedJob === "all") {
        const results = await Promise.all(
          jobs.map((j) =>
            listCandidates(j.job_id)
              .then((rows) => rows.map((c) => ({ ...c, jobId: j.job_id })))
              .catch(() => [])
          )
        );
        const seen = new Set<string>();
        return results.flat().filter((c) => {
          if (seen.has(c.id)) return false;
          seen.add(c.id);
          return true;
        });
      }
      const rows = await listCandidates(selectedJob).catch(() => []);
      return rows.map((c) => ({ ...c, jobId: selectedJob }));
    };

    fetchAll()
      .then(setCandidates)
      .finally(() => setLoading(false));
  }, [selectedJob, jobs]);

  const filtered = useMemo(() => {
    const st = parseStatusFilter(statusFilter);
    const min = minScore === "" ? null : Number(minScore);
    return candidates.filter((c) => {
      if (st !== "all" && c.status.toLowerCase() !== st) return false;
      if (min !== null && !Number.isNaN(min) && c.score < min) return false;
      if (sourceFilter !== "all") {
        const source = c.source_platform || "manual";
        if (sourceFilter !== source) return false;
      }
      return true;
    });
  }, [candidates, statusFilter, minScore, sourceFilter]);

  const needsAction = filtered.filter(
    (c) => !confirmedIds.has(c.id)
  );
  const actionCount = needsAction.length;

  function defaultSlots(): string[] {
    const mk = (d: number, h: number) => {
      const x = new Date();
      x.setDate(x.getDate() + d);
      x.setHours(h, 0, 0, 0);
      return x.toISOString();
    };
    return [mk(1, 10), mk(1, 14), mk(2, 10)];
  }

  async function handleConnectGoogle() {
    try {
      const { auth_url } = await getGoogleAuthUrl();
      window.open(auth_url, "_blank", "noopener");
    } catch {
      // ignore
    }
  }

  async function handleSyncNaukri() {
    setSyncing(true);
    try {
      // Sync for all jobs (don't need to select a specific job)
      const result = await syncNaukriCandidates("", "");
      console.log("Sync completed:", result);

      // Wait a moment for the database to be updated
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Refresh all candidates
      if (selectedJob === "all") {
        const results = await Promise.all(
          jobs.map((j) =>
            listCandidates(j.job_id)
              .then((rows) => rows.map((c) => ({ ...c, jobId: j.job_id })))
              .catch(() => [])
          )
        );
        const seen = new Set<string>();
        const allCandidates = results.flat().filter((c) => {
          if (seen.has(c.id)) return false;
          seen.add(c.id);
          return true;
        });
        setCandidates(allCandidates);
      } else {
        const rows = await listCandidates(selectedJob).catch(() => []);
        setCandidates(rows.map((c) => ({ ...c, jobId: selectedJob })));
      }

      alert(`✅ Sync completed! ${result.message}`);
    } catch (error) {
      console.error("Sync failed:", error);
      alert(`❌ Failed to sync candidates: ${error}`);
    } finally {
      setSyncing(false);
    }
  }

  async function handleScheduleAll() {
    if (actionCount === 0) return;
    setScheduling(true);
    const newConfirmed = new Set(confirmedIds);
    const newTokens = new Map(inviteTokens);
    const slots = defaultSlots();

    for (const c of needsAction) {
      try {
        const existingToken = newTokens.get(c.id);
        if (existingToken) {
          await sendSchedulingEmail(existingToken);
        } else {
          const inv = await createAvailabilityInvite({
            candidate_id: c.id,
            posted_job_id: c.jobId,
            proposed_slots: slots,
          });
          newTokens.set(c.id, inv.token);
        }
        newConfirmed.add(c.id);
      } catch {
        // skip failed ones
      }
    }

    setConfirmedIds(new Set(newConfirmed));
    setInviteTokens(new Map(newTokens));
    setScheduling(false);
  }

  const rows = filtered.map((c) => ({
    id: c.id,
    name: c.name,
    matchScore: c.score,
    status: c.status.toLowerCase() as "shortlist" | "review" | "reject",
    postedJobId: c.jobId,
    title: "",
    yearsExperience: 0,
    email: "",
    phone: c.phone_number ?? "",
    experienceSummary: c.summary ?? "",
    source_platform: c.source_platform,
    skills: [],
    decisionReasons: [],
    skillsOverlapWithJD: [],
    skillsMissingFromResume: [],
  }));

  const allScheduled = actionCount === 0 && candidates.length > 0;

  return (
    <>
      <TopBar
        title="Candidates"
        subtitle="Review AI match scores and pipeline status."
        actions={
          googleConnected === false ? (
            <button
              type="button"
              onClick={handleConnectGoogle}
              className="inline-flex items-center gap-2 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-4 py-2 text-sm font-semibold text-[var(--hp-text)] shadow-sm hover:bg-[var(--hp-surface)] transition-colors"
            >
              Connect Google
            </button>
          ) : (
            <button
              type="button"
              onClick={handleScheduleAll}
              disabled={scheduling || allScheduled || candidates.length === 0 || selectedJob === "all"}
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--hp-accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {scheduling
                ? "Sending invites…"
                : allScheduled
                  ? "All invites sent"
                  : `+ Schedule all (${actionCount})`}
            </button>
          )
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
        <div>
          <label
            htmlFor="job-filter"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Job
          </label>
          <select
            id="job-filter"
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
          >
            <option value="all">All jobs</option>
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.title || j.job_id}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={handleSyncNaukri}
          disabled={syncing}
          className="rounded-lg border border-[var(--hp-accent)] bg-[var(--hp-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          title="Sync candidates from Naukri for ALL open jobs"
        >
          {syncing ? (
            <>
              <span className="hp-spinner">⟳</span>
              Syncing...
            </>
          ) : (
            <>
              ↓ Sync
            </>
          )}
        </button>

        <div>
          <label
            htmlFor="status-filter"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
          >
            <option value="all">All</option>
            <option value="shortlist">Shortlist</option>
            <option value="review">Review</option>
            <option value="reject">Reject</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="source-filter"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Source
          </label>
          <select
            id="source-filter"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
          >
            <option value="all">All</option>
            <option value="manual">Manual Upload</option>
            <option value="naukri">Naukri</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="score-min"
            className="mb-1 block text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]"
          >
            Min score %
          </label>
          <input
            id="score-min"
            type="number"
            min={0}
            max={100}
            placeholder="e.g. 70"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            className="w-32 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
          />
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-[var(--hp-text-muted)]">Loading candidates…</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-[var(--hp-text-muted)]">
          No candidates yet. Upload a resume on the Upload page.
        </p>
      ) : (
        <DataTable rows={rows} />
      )}
    </>
  );
}
