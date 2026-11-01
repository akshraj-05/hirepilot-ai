"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SkillsBreakdown } from "@/components/candidate/SkillsBreakdown";
import { AvailabilityInviteLink } from "@/components/candidate/AvailabilityInviteLink";
import { FeedbackPanel } from "@/components/candidate/FeedbackPanel";
import { ScheduleMeetingModal } from "@/components/meetings/ScheduleMeetingModal";
import { getCandidate, listMeetings } from "@/utils/api";
import type { CandidateStatus } from "@/utils/types";

type CandidateDetail = {
  id: string;
  name: string;
  skills: string[];
  score: number;
  status: string;
  matched_skills: string[];
  missing_skills: string[];
  summary: string;
  project_summary: string | null;
  work_summary: string | null;
  red_flags: string[];
  green_flags: string[];
};

/** Candidate detail — fetched from backend. */
export default function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;

  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasMeeting, setHasMeeting] = useState(false);

  useEffect(() => {
    if (!id) return;
    getCandidate(id, jobId)
      .then((data) => {
        setCandidate({
          ...data,
          red_flags: Array.isArray(data.red_flags) ? data.red_flags : [],
          green_flags: Array.isArray(data.green_flags) ? data.green_flags : [],
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
    listMeetings()
      .then((meetings) => setHasMeeting(meetings.some((m) => m.candidate_id === id)))
      .catch(() => {});
  }, [id, jobId]);

  function onMeetingCreated() {
    setHasMeeting(true);
  }

  if (loading) {
    return (
      <p className="mt-8 text-sm text-[var(--hp-text-muted)]">
        Loading candidate…
      </p>
    );
  }
  if (error || !candidate) {
    return (
      <p className="mt-8 text-sm text-red-600">
        {error ?? "Candidate not found."}
      </p>
    );
  }

  const status = candidate.status.toLowerCase() as CandidateStatus;

  return (
    <>
      <div className="mb-4">
        <Link
          href="/candidates"
          className="text-sm font-medium text-[var(--hp-accent)] hover:underline"
        >
          ← Candidates
        </Link>
      </div>

      <TopBar
        title={candidate.name}
        subtitle={`Match score: ${candidate.score}%`}
        actions={
          <ScheduleMeetingModal
            candidateId={candidate.id}
            candidateName={candidate.name}
            jobId={jobId}
            disabled={hasMeeting}
            onCreated={onMeetingCreated}
          />
        }
      />

      {/* Defensive parsing for flags in case of stringified JSON */}
      {(() => {
        try {
          const ensureStringArray = (val: any): string[] => {
            if (Array.isArray(val)) {
              return val.flatMap((item) => {
                if (typeof item === "string") {
                  try {
                    const parsed = JSON.parse(item);
                    if (Array.isArray(parsed)) return parsed;
                    if (typeof parsed === "object" && parsed !== null)
                      return Object.values(parsed).filter((v) => typeof v === "string");
                  } catch {}
                  return [item];
                }
                return [];
              });
            }
            return [];
          };
          candidate.red_flags = ensureStringArray(candidate.red_flags);
          candidate.green_flags = ensureStringArray(candidate.green_flags);
        } catch {}
        return null;
      })()}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card title="Resume skills">
            {candidate.skills.length > 0 ? (
              <ul className="flex flex-wrap gap-2">
                {candidate.skills.map((s) => (
                  <li
                    key={s}
                    className="rounded-md bg-[var(--hp-surface)] px-2 py-1 text-xs text-[var(--hp-text-muted)]"
                  >
                    {s}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-[var(--hp-text-muted)]">
                Skills will appear after parsing the resume.
              </p>
            )}
          </Card>

          <Card
            title="Match score"
            description="AI score for this candidate vs the job."
          >
            <div className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] p-4">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-4xl font-bold tabular-nums text-[var(--hp-text)]">
                  {candidate.score}%
                </span>
                <Badge status={status} />
              </div>
              <div className="mt-4">
                <ProgressBar value={candidate.score} />
              </div>
            </div>
          </Card>

          {(candidate.summary || candidate.project_summary || candidate.work_summary) && (
            <Card title="AI summary">
              <div className="space-y-4">
                {candidate.summary && (
                  <p className="text-sm leading-relaxed text-[var(--hp-text)]">
                    {candidate.summary}
                  </p>
                )}
                {candidate.work_summary && (
                  <div>
                    <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                      Work Summary
                    </h4>
                    <p className="text-sm leading-relaxed text-[var(--hp-text)]">
                      {candidate.work_summary}
                    </p>
                  </div>
                )}
                {candidate.project_summary && (
                  <div>
                    <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                      Project Summary
                    </h4>
                    <p className="text-sm leading-relaxed text-[var(--hp-text)]">
                      {candidate.project_summary}
                    </p>
                  </div>
                )}
              </div>
            </Card>
          )}
          {(candidate.green_flags?.length > 0 || candidate.red_flags?.length > 0) && (
            <Card title="Flags">
              <div className="space-y-4">
                {candidate.green_flags?.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                      🟢Green Flags
                    </h4>
                    <ul className="space-y-1">
                      {candidate.green_flags.map((flag, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-[var(--hp-text)]">
                          <span className="mt-0.5 text-green-500">•</span>
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {candidate.red_flags?.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                      🔴 Red Flags
                    </h4>
                    <ul className="space-y-1">
                      {candidate.red_flags.map((flag, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-[var(--hp-text)]">
                          <span className="mt-0.5 text-red-500">•</span>
                          {flag}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          )}
          <SkillsBreakdown
            matched={candidate.matched_skills}
            missing={candidate.missing_skills}
          />
        </div>

        <div className="lg:col-span-1 space-y-6">
          <FeedbackPanel
            initialStatus={status}
            candidateName={candidate.name}
            candidateId={candidate.id}
            jobId={jobId ?? ""}
          />
          <Card title="Invitation link">
            <AvailabilityInviteLink candidateId={candidate.id} postedJobId={jobId} />
          </Card>
        </div>
      </div>
    </>
  );
}
