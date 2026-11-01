"use client";

import { useEffect, useState } from "react";
import { FileUploader } from "@/components/ui/FileUploader";
import { Card } from "@/components/ui/Card";
import { createJob, listJobs, uploadResume, runOrchestrator } from "@/utils/api";

type PipelineStage = "idle" | "uploading" | "uploaded" | "analyzing" | "done";

/**
 * Upload a resume, pick or create a job, then run AI analysis.
 * All steps call the real backend API.
 */
export function UploadAnalyzeForm() {
  const [jobs, setJobs] = useState<{ job_id: string; title: string }[]>([]);
  const [jobMode, setJobMode] = useState<"existing" | "new">("new");
  const [selectedJobId, setSelectedJobId] = useState<string>("");
  const [newJobTitle, setNewJobTitle] = useState<string>("");
  const [newJobDesc, setNewJobDesc] = useState<string>("");
  const [candidateName, setCandidateName] = useState<string>("");
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [error, setError] = useState<string | null>(null);

  const busy = stage !== "idle" && stage !== "done";

  useEffect(() => {
    listJobs()
      .then((data) => {
        setJobs(data);
        if (data.length > 0) {
          setJobMode("existing");
          setSelectedJobId(data[0].job_id);
        }
      })
      .catch(() => { });
  }, []);

  const handleFileChange = (picked: File | null) => {
    setFile(picked);
    if (picked && !candidateName.trim()) {
      const name = picked.name
        .replace(/\.[^.]+$/, "")
        .replace(/[_-]+/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      setCandidateName(name);
    }
  };

  const onSubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault();
    if (!file) return;
    setStage("uploading");
    setError(null);

    try {
      let jobId = selectedJobId;
      if (jobMode === "new") {
        if (!newJobTitle.trim() || !newJobDesc.trim()) {
          setError("Please fill in job title and description.");
          setStage("idle");
          return;
        }
        const j = await createJob(newJobTitle.trim(), newJobDesc.trim());
        jobId = j.job_id;
        const updated = await listJobs();
        setJobs(updated);
        setSelectedJobId(jobId);
        setJobMode("existing");
      }

      const uploaded = await uploadResume(file, candidateName.trim(), jobId);

      setStage("uploaded");

      await new Promise((r) => setTimeout(r, 1200));

      setStage("analyzing");

      await runOrchestrator(uploaded.candidate_id, jobId);

      setStage("done");
      setFile(null);
      setCandidateName("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStage("idle");
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {/* Job selection */}
      <Card title="Job" description="Pick an existing job or create a new one.">
        <div className="flex gap-4 mb-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="radio"
              name="job-mode"
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
              name="job-mode"
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

      {/* Candidate name */}
      <Card title="Candidate name" description="Auto-filled from filename.">
        <input
          type="text"
          placeholder="e.g. Jane Smith"
          value={candidateName}
          onChange={(e) => setCandidateName(e.target.value)}
          className="w-full rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-3 py-2 text-sm text-[var(--hp-text)] focus:outline-none"
        />
      </Card>

      {/* Resume upload */}
      <Card title="Resume" description="Upload a PDF or DOCX file.">
        <FileUploader
          multiple={false}
          onFilesSelected={(files) => handleFileChange(files[0] ?? null)}
          reset={stage === "done"}
        />
        {file && (
          <p className="mt-2 text-xs text-[var(--hp-text-muted)]">
            Selected: {file.name}
          </p>
        )}
      </Card>

      <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
        <button
          type="submit"
          disabled={busy || !file || stage === "done"}
          className="inline-flex items-center justify-center rounded-lg bg-[var(--hp-accent)] px-5 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Analyze candidate
        </button>

        {error && (
          <p className="text-sm text-red-600">{error}</p>
        )}
      </div>

      {/* Step-by-step pipeline status */}
      {stage !== "idle" && (
        <Card className="mt-2">
          <div className="space-y-3">
            <StageRow
              label="Uploading & parsing resume"
              state={
                stage === "uploading"
                  ? "loading"
                  : stage === "uploaded" || stage === "analyzing" || stage === "done"
                    ? "done"
                    : "pending"
              }
              doneText="Resume uploaded successfully"
            />
            <StageRow
              label="Analyzing in progress"
              state={
                stage === "analyzing"
                  ? "loading"
                  : stage === "done"
                    ? "done"
                    : "pending"
              }
              doneText="Analysis complete"
            />
          </div>
        </Card>
      )}

    </form>
  );
}

function StageRow({
  label,
  state,
  doneText,
}: {
  label: string;
  state: "pending" | "loading" | "done";
  doneText: string;
}) {
  return (
    <div className="flex items-center gap-3">
      {state === "loading" && (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-[var(--hp-accent)]" />
      )}
      {state === "done" && (
        <svg
          className="h-4 w-4 text-emerald-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
      {state === "pending" && (
        <div className="h-4 w-4 rounded-full border-2 border-slate-200" />
      )}
      <span
        className={`text-sm ${state === "done"
            ? "font-medium text-emerald-600"
            : state === "loading"
              ? "text-[var(--hp-text)]"
              : "text-[var(--hp-text-muted)]"
          }`}
      >
        {state === "done" ? doneText : label}
      </span>
    </div>
  );
}
