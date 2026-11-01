"use client";

import { useState } from "react";
import type { CandidateStatus } from "@/utils/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { submitFeedback, updateCandidateStatus } from "@/utils/api";

type FeedbackPanelProps = {
  initialStatus: CandidateStatus;
  candidateName: string;
  candidateId: string;
  jobId: string;
};

/** Human-in-the-loop controls: override decision + rate AI correctness. */
export function FeedbackPanel({
  initialStatus,
  candidateName,
  candidateId,
  jobId,
}: FeedbackPanelProps) {
  const [status, setStatus] = useState<CandidateStatus>(initialStatus);
  const [aiRating, setAiRating] = useState<"unset" | "correct" | "incorrect">(
    "unset",
  );
  const [msg, setMsg] = useState<string | null>(null);

  const showMsg = (text: string) => {
    setMsg(text);
    window.setTimeout(() => setMsg(null), 2800);
  };

  const handleStatusOverride = async (newStatus: CandidateStatus) => {
    setStatus(newStatus);
    try {
      await updateCandidateStatus(candidateId, jobId, newStatus);
      showMsg(`Status updated to ${newStatus}`);
    } catch {
      showMsg("Could not save — check backend connection.");
    }
  };

  const handleAiRating = async (correct: boolean) => {
    const rating = correct ? "correct" : "incorrect";
    setAiRating(rating);
    try {
      await submitFeedback(candidateId, jobId, correct);
      showMsg(`Marked AI decision as ${rating}`);
    } catch {
      showMsg("Could not save — check backend connection.");
    }
  };

  return (
    <Card
      title="Feedback & overrides"
      description={`Adjust pipeline for ${candidateName}.`}
    >
      <div className="space-y-6">
        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
            Current decision
          </p>
          <Badge status={status} />
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
            Override decision
          </p>
          <div className="flex flex-wrap gap-2">
            {(
              [
                ["shortlist", "Shortlist"],
                ["review", "Review"],
                ["reject", "Reject"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                onClick={() => handleStatusOverride(value)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  status === value
                    ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)] text-[var(--hp-accent)]"
                    : "border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] text-[var(--hp-text)] hover:bg-[var(--hp-surface)]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
            Was the AI decision right?
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleAiRating(true)}
              className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                aiRating === "correct"
                  ? "border-[var(--hp-shortlist)] bg-[var(--hp-shortlist-bg)] text-[var(--hp-shortlist)]"
                  : "border-[var(--hp-border)] hover:bg-[var(--hp-surface)]"
              }`}
            >
              Correct
            </button>
            <button
              type="button"
              onClick={() => handleAiRating(false)}
              className={`rounded-lg border px-3 py-2 text-sm font-medium ${
                aiRating === "incorrect"
                  ? "border-[var(--hp-reject)] bg-[var(--hp-reject-bg)] text-[var(--hp-reject)]"
                  : "border-[var(--hp-border)] hover:bg-[var(--hp-surface)]"
              }`}
            >
              Incorrect
            </button>
          </div>
        </div>

        {msg && (
          <p className="text-sm text-[var(--hp-text-muted)]" role="status">
            {msg}
          </p>
        )}
      </div>
    </Card>
  );
}
