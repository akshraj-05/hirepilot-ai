"use client";


import { useEffect, useRef, useState } from "react";
import { Card } from "@/components/ui/Card";
import { createJob, listJobs } from "@/utils/api";
import { getOrgId } from "@/utils/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

type JobRow = { job_id: string; title: string };

type ResumeResult = {
  filename: string;
  status: "success" | "skipped";
  reason?: string;
};

type Phase =
  | { kind: "idle" }
  | { kind: "uploading" }
  | { kind: "processing"; current: number; total: number; log: ResumeResult[] }
  | { kind: "done"; total: number; success: number; skipped: number; log: ResumeResult[] }
  | { kind: "error"; message: string };

export function ZipUploadForm() {
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [jobMode, setJobMode] = useState<"existing" | "new">("new");
  const [selectedJobId, setSelectedJobId] = useState("");
  const [newJobTitle, setNewJobTitle] = useState("");
  const [newJobDesc, setNewJobDesc] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [phase, setPhase] = useState<Phase>({ kind: "idle" });
  const logRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const busy = phase.kind === "uploading" || phase.kind === "processing";

  useEffect(() => {
    listJobs()
      .then((data) => {
        setJobs(data);
        if (data.length > 0) {
          setJobMode("existing");
          setSelectedJobId(data[0].job_id);
        }
      })
      .catch(() => {});
  }, []);

  // Auto-scroll log to bottom as new entries arrive
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [phase]);

  // Clear file picker when upload completes
  useEffect(() => {
    if (phase.kind === "done") {
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }, [phase.kind]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setPhase({ kind: "uploading" });

    try {
      let jobId = selectedJobId;
      if (jobMode === "new") {
        if (!newJobTitle.trim() || !newJobDesc.trim()) {
          setPhase({ kind: "error", message: "Please fill in job title and description." });
          return;
        }
        const j = await createJob(newJobTitle.trim(), newJobDesc.trim());
        jobId = j.job_id;
        const updated = await listJobs();
        setJobs(updated);
        setSelectedJobId(jobId);
        setJobMode("existing");
      }

      const form = new FormData();
      form.append("file", file);
      form.append("job_id", jobId);
      form.append("organization_id", getOrgId());

      const res = await fetch(`${BASE_URL}/api/candidates/zip-upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok || !res.body) {
        const text = await res.text().catch(() => "Upload failed");
        setPhase({ kind: "error", message: text });
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      const log: ResumeResult[] = [];

      const handleSSE = (line: string) => {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) return;
        try {
          const event = JSON.parse(trimmed.slice(6));

          if (event.type === "start") {
            setPhase({ kind: "processing", current: 0, total: event.total, log: [] });
          } else if (event.type === "progress") {
            const entry: ResumeResult = {
              filename: event.filename,
              status: event.status,
              reason: event.reason,
            };
            log.push(entry);
            setPhase({
              kind: "processing",
              current: event.current,
              total: event.total,
              log: [...log],
            });
          } else if (event.type === "complete") {
            setPhase({
              kind: "done",
              total: event.total,
              success: event.success,
              skipped: event.skipped,
              log: [...log],
            });
          } else if (event.type === "error") {
            setPhase({ kind: "error", message: event.message });
          }
        } catch {
          // malformed SSE line — skip
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";
        for (const part of parts) handleSSE(part);
      }

      // Process any remaining data in the buffer after stream closes
      if (buffer.trim()) handleSSE(buffer);

    } catch (err: unknown) {
      setPhase({
        kind: "error",
        message: err instanceof Error ? err.message : "Something went wrong.",
      });
    }
  };

  const progressPct =
    phase.kind === "processing" && phase.total > 0
      ? Math.round((phase.current / phase.total) * 100)
      : 0;

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Job selection */}
      <Card title="Job" description="Pick an existing job or create a new one.">
        <div className="flex gap-4 mb-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="radio"
              name="zip-job-mode"
              value="existing"
              checked={jobMode === "existing"}
              onChange={() => setJobMode("existing")}
              disabled={jobs.length === 0}
            />
            Use existing job
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="radio"
              name="zip-job-mode"
              value="new"
              checked={jobMode === "new"}
              onChange={() => setJobMode("new")}
            />
            Create new job
          </label>
        </div>

        {jobMode === "existing" && jobs.length > 0 ? (
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
          >
            {jobs.map((j) => (
              <option key={j.job_id} value={j.job_id}>
                {j.title || j.job_id}
              </option>
            ))}
          </select>
        ) : (
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Job title"
              value={newJobTitle}
              onChange={(e) => setNewJobTitle(e.target.value)}
              className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
            />
            <textarea
              rows={4}
              placeholder="Job description…"
              value={newJobDesc}
              onChange={(e) => setNewJobDesc(e.target.value)}
              className="w-full resize-y rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
            />
          </div>
        )}
      </Card>

      {/* ZIP file picker */}
      <Card title="Resume ZIP" description="Upload a ZIP file containing PDF or DOCX resumes. Processed in batches of 10.">
        <label
          className={`flex cursor-pointer flex-col items-center justify-center rounded-[var(--hp-radius)] border-2 border-dashed px-6 py-12 transition-colors ${
            file
              ? "border-[var(--hp-accent)] bg-[var(--hp-accent-muted)]"
              : "border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] hover:border-[var(--hp-accent)]"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            className="sr-only"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <span className="text-sm font-medium text-[var(--hp-text)]">
            Drop a ZIP here or click to browse
          </span>
          <span className="mt-1 text-xs text-[var(--hp-text-muted)]">
            ZIP containing PDF or DOCX files only
          </span>
        </label>
        {file && (
          <p className="mt-2 text-xs text-[var(--hp-text-muted)]">
            Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </Card>

      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={busy || !file || phase.kind === "done"}
          className="inline-flex items-center justify-center rounded-lg bg-[var(--hp-accent)] px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "Processing…" : "Upload & analyze"}
        </button>

        {phase.kind === "error" && (
          <p className="text-sm text-red-600">{phase.message}</p>
        )}
      </div>

      {/* Live progress */}
      {(phase.kind === "uploading" || phase.kind === "processing" || phase.kind === "done") && (
        <Card>
          <div className="space-y-4">
            {/* Header counts */}
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-[var(--hp-text)]">
                {phase.kind === "uploading"
                  ? "Uploading ZIP…"
                  : phase.kind === "processing"
                  ? `Processing ${phase.current} / ${phase.total} resumes`
                  : `Done — ${phase.success} analyzed, ${phase.skipped} skipped`}
              </span>
              {phase.kind === "processing" && (
                <span className="text-[var(--hp-text-muted)]">{progressPct}%</span>
              )}
              {phase.kind === "done" && (
                <span className="text-emerald-600 font-medium">Complete</span>
              )}
            </div>

            {/* Progress bar */}
            {(phase.kind === "processing" || phase.kind === "done") && (
              <div className="h-2 w-full rounded-full bg-[var(--hp-border)] overflow-hidden">
                <div
                  className="h-2 rounded-full bg-[var(--hp-accent)] transition-all duration-300"
                  style={{
                    width:
                      phase.kind === "done"
                        ? "100%"
                        : `${progressPct}%`,
                  }}
                />
              </div>
            )}

            {/* Scrollable log */}
            {(phase.kind === "processing" || phase.kind === "done") && (
              <div
                ref={logRef}
                className="max-h-64 overflow-y-auto space-y-1.5 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] p-3"
              >
                {phase.log.length === 0 && (
                  <p className="text-xs text-[var(--hp-text-muted)]">Starting…</p>
                )}
                {phase.log.map((r, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    {r.status === "success" && !r.reason ? (
                      <svg className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : r.status === "success" && r.reason ? (
                      <svg className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      </svg>
                    )}
                    <span className={r.status === "success" ? "text-[var(--hp-text)]" : "text-amber-700"}>
                      <span className="font-medium">{r.filename}</span>
                      {r.reason && (
                        <span className="ml-1 text-[var(--hp-text-muted)]">— {r.reason}</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {/* Summary pills */}
            {phase.kind === "done" && (
              <div className="flex gap-3">
                <span className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                  {phase.success} analyzed
                </span>
                {phase.skipped > 0 && (
                  <span className="inline-flex items-center rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                    {phase.skipped} skipped
                  </span>
                )}
              </div>
            )}
          </div>
        </Card>
      )}
    </form>
  );
}
