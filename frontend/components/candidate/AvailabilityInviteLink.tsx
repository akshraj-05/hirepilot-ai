"use client";

import { useEffect, useMemo, useState } from "react";
import { checkCandidateInvite, createAvailabilityInvite } from "@/utils/api";

function defaultSlots(): string[] {
  const mk = (d: number, h: number) => {
    const x = new Date();
    x.setDate(x.getDate() + d);
    x.setHours(h, 0, 0, 0);
    return x.toISOString();
  };
  return [mk(1, 10), mk(1, 14), mk(2, 10)];
}

type Props = { candidateId: string; postedJobId: string | undefined };

/** One control: copy invitation URL for the candidate to mark availability from offered slots. */
export function AvailabilityInviteLink({ candidateId, postedJobId }: Props) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [existingToken, setExistingToken] = useState<string | null>(null);

  const slots = useMemo(() => defaultSlots(), []);

  useEffect(() => {
    setExistingToken(null);
    if (!candidateId || !postedJobId) return;
    checkCandidateInvite(candidateId, postedJobId)
      .then((r) => { if (r.has_invite && r.token) setExistingToken(r.token); })
      .catch(() => {});
  }, [candidateId, postedJobId]);

  async function copyLink() {
    if (!postedJobId) return;
    setBusy(true);
    setErr(null);
    try {
      let path: string;
      if (existingToken) {
        path = `/scheduling/${existingToken}`;
      } else {
        const inv = await createAvailabilityInvite({
          candidate_id: candidateId,
          posted_job_id: postedJobId,
          proposed_slots: slots,
        });
        path = inv.path;
        setExistingToken(inv.token);
      }
      const url = `${typeof window !== "undefined" ? window.location.origin : ""}${path}`;
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2500);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  if (!postedJobId) {
    return (
      <p className="text-sm text-[var(--hp-text-muted)]">
        Select a job from the candidates list so this invite is tied to a role.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={copyLink}
        disabled={busy}
        className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm font-medium text-[var(--hp-text)] hover:bg-[var(--hp-surface)] disabled:opacity-50"
      >
        {busy ? "Working…" : copied ? "Copied" : "Copy invitation link"}
      </button>
      <p className="text-xs text-[var(--hp-text-muted)]">
        Paste into your invite email. The candidate opens the link and picks one of the offered times.
      </p>
      {err && <p className="text-xs text-red-600">{err}</p>}
    </div>
  );
}
