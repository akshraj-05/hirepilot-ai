"use client";

import { useEffect, useMemo, useState } from "react";
import {
  checkCandidateInvite,
  createAvailabilityInvite,
  getGoogleAuthStatus,
  getGoogleAuthUrl,
  sendSchedulingEmail,
} from "@/utils/api";

type Props = {
  candidateId?: string;
  candidateName?: string;
  jobId?: string;
  disabled?: boolean;
  onCreated?: () => void;
};

function defaultSlots(): string[] {
  const mk = (d: number, h: number) => {
    const x = new Date();
    x.setDate(x.getDate() + d);
    x.setHours(h, 0, 0, 0);
    return x.toISOString();
  };
  return [mk(1, 10), mk(1, 14), mk(2, 10)];
}

type FlowState = "idle" | "sending" | "sent" | "error";

export function ScheduleMeetingModal({
  candidateId,
  candidateName,
  jobId,
  disabled = false,
  onCreated,
}: Props) {
  const [flowState, setFlowState] = useState<FlowState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [googleConnected, setGoogleConnected] = useState<boolean | null>(null);
  const [alreadyInvited, setAlreadyInvited] = useState(false);

  const slots = useMemo(() => defaultSlots(), []);
  const [pendingToken, setPendingToken] = useState<string | null>(null);

  useEffect(() => {
    getGoogleAuthStatus()
      .then((s) => setGoogleConnected(s.connected))
      .catch(() => setGoogleConnected(false));
  }, []);

  useEffect(() => {
    setAlreadyInvited(false);
    setPendingToken(null);
    setFlowState("idle");
    setErrorMsg(null);

    if (!candidateId || !jobId) return;
    checkCandidateInvite(candidateId, jobId)
      .then((r) => {
        if (r.has_invite) {
          setAlreadyInvited(true);
          if (r.token) setPendingToken(r.token);
        }
      })
      .catch(() => {});
  }, [candidateId, jobId]);

  async function connectGoogle() {
    try {
      const { auth_url } = await getGoogleAuthUrl();
      window.open(auth_url, "_blank", "noopener");
    } catch (e) {
      setErrorMsg(
        e instanceof Error ? e.message : "Could not get Google auth URL"
      );
    }
  }

  async function handleSchedule() {
    if (!candidateId || !jobId) return;
    setFlowState("sending");
    setErrorMsg(null);
    try {
      if (pendingToken) {
        await sendSchedulingEmail(pendingToken);
      } else {
        const inv = await createAvailabilityInvite({
          candidate_id: candidateId,
          posted_job_id: jobId,
          proposed_slots: slots,
        });
        setPendingToken(inv.token);
      }
      setFlowState("sent");
      setAlreadyInvited(true);
      onCreated?.();
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Failed to send invite");
      setFlowState("error");
    }
  }

  if (googleConnected === false) {
    return (
      <div className="inline-flex flex-col items-start gap-1">
        <button
          type="button"
          onClick={connectGoogle}
          className="inline-flex items-center gap-2 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-4 py-2 text-sm font-semibold text-[var(--hp-text)] shadow-sm hover:bg-[var(--hp-surface)] transition-colors"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Connect Google
        </button>
        <p className="text-xs text-[var(--hp-text-muted)]">
          Connect Google to send scheduling emails and create calendar events.
        </p>
      </div>
    );
  }

  const isDisabled =
    disabled ||
    alreadyInvited ||
    flowState === "sent" ||
    flowState === "sending" ||
    !candidateId ||
    !jobId;

  const label =
    flowState === "sending"
      ? "Sending invite…"
      : flowState === "sent" || alreadyInvited
        ? "Invite sent"
        : "+ Schedule meeting";

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={handleSchedule}
        disabled={isDisabled}
        className="inline-flex items-center gap-2 rounded-lg bg-[var(--hp-accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {label}
      </button>
      {(flowState === "sent" || alreadyInvited) && flowState !== "error" && (
        <p className="text-xs text-green-600">
          Scheduling email sent to {candidateName ?? "the candidate"}.
        </p>
      )}
      {errorMsg && (
        <p className="max-w-xs text-xs text-red-600">{errorMsg}</p>
      )}
    </div>
  );
}
