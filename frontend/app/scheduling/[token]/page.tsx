"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { chooseAvailabilitySlot, getAvailabilityInvite } from "@/utils/api";

function label(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export default function AvailabilityPage() {
  const { token } = useParams<{ token: string }>();
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [invite, setInvite] = useState<Awaited<ReturnType<typeof getAvailabilityInvite>> | null>(
    null
  );
  const [pick, setPick] = useState("");
  const [saving, setSaving] = useState(false);
  const [doneMsg, setDoneMsg] = useState<string | null>(null);
  const [meetLink, setMeetLink] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    getAvailabilityInvite(token)
      .then((d) => {
        setInvite(d);
        if (d.proposed_slots[0]) setPick(d.proposed_slots[0]);
      })
      .catch(() => setErr("Invalid or expired link."))
      .finally(() => setLoading(false));
  }, [token]);

  async function submit() {
    if (!token || !pick) return;
    setSaving(true);
    setErr(null);
    try {
      const r = await chooseAvailabilitySlot(token, pick);
      setDoneMsg(r.message);
      if (r.meeting_link) setMeetLink(r.meeting_link);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not save");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center text-sm text-[var(--hp-text-muted)]">
        Loading…
      </main>
    );
  }

  if (err && !invite) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center text-sm text-red-600">{err}</main>
    );
  }

  if (!invite) return null;

  if (invite.status === "confirmed" || doneMsg) {
    return (
      <main className="mx-auto max-w-md px-4 py-16">
        <div className="rounded-xl border border-green-200 bg-green-50 p-6">
          <h1 className="text-lg font-semibold text-green-800">All set!</h1>
          <p className="mt-2 text-sm text-green-700">
            {doneMsg ?? "Your response was recorded."}
          </p>
          {meetLink && (
            <a
              href={meetLink}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden>
                <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z" />
              </svg>
              Join Google Meet
            </a>
          )}
          <p className="mt-3 text-xs text-green-600">
            A calendar invite has been sent to your email.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-xl font-semibold text-[var(--hp-text)]">Your availability</h1>
      <p className="mt-2 text-sm text-[var(--hp-text-muted)]">
        {invite.candidate_name?.trim()
          ? `${invite.candidate_name.split(/\s+/)[0]}, `
          : ""}
        choose one time for{" "}
        <span className="font-medium text-[var(--hp-text)]">{invite.job_title}</span>.
      </p>

      <div className="mt-6 space-y-2">
        {invite.proposed_slots.map((s) => (
          <label
            key={s}
            className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 text-sm ${
              pick === s ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)]" : "border-[var(--hp-border)]"
            }`}
          >
            <input type="radio" name="slot" checked={pick === s} onChange={() => setPick(s)} />
            <span>{label(s)}</span>
          </label>
        ))}
      </div>

      {err && <p className="mt-4 text-sm text-red-600">{err}</p>}

      <button
        type="button"
        onClick={submit}
        disabled={saving || !pick}
        className="mt-6 w-full rounded-lg bg-[var(--hp-accent)] py-3 text-sm font-semibold text-white disabled:opacity-50"
      >
        {saving ? "Saving…" : "Submit"}
      </button>
    </main>
  );
}
