"use client";

import { useState } from "react";
import { TopBar } from "@/components/layout/TopBar";
import { UploadAnalyzeForm } from "@/components/upload/UploadAnalyzeForm";
import { ZipUploadForm } from "@/components/upload/ZipUploadForm";

type Tab = "single" | "bulk";

export default function UploadPage() {
  const [tab, setTab] = useState<Tab>("single");

  return (
    <>
      <TopBar
        title="Upload & analyze"
        subtitle="Add resumes and align them to your open role."
      />

      {/* Tab switcher */}
      <div className="flex gap-1 mb-6 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] p-1 w-fit shadow-[var(--hp-shadow)]">
        <button
          type="button"
          onClick={() => setTab("single")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            tab === "single"
              ? "bg-[var(--hp-accent)] text-white shadow-sm"
              : "text-[var(--hp-text-muted)] hover:text-[var(--hp-text)]"
          }`}
        >
          Single resume
        </button>
        <button
          type="button"
          onClick={() => setTab("bulk")}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            tab === "bulk"
              ? "bg-[var(--hp-accent)] text-white shadow-sm"
              : "text-[var(--hp-text-muted)] hover:text-[var(--hp-text)]"
          }`}
        >
          Bulk ZIP upload
        </button>
      </div>

      {tab === "single" ? <UploadAnalyzeForm /> : <ZipUploadForm />}
    </>
  );
}
