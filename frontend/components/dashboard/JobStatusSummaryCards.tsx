import { Card } from "@/components/ui/Card";
import type { JobPostingStatus } from "@/utils/types";

type Counts = Record<JobPostingStatus, number>;

type JobStatusSummaryCardsProps = {
  counts: Counts;
};

const items: {
  key: JobPostingStatus;
  label: string;
  accent: string;
}[] = [
  { key: "open", label: "Open roles", accent: "text-[var(--hp-shortlist)]" },
  { key: "closed", label: "Closed", accent: "text-slate-600" },
  { key: "draft", label: "Drafts", accent: "text-[var(--hp-review)]" },
  { key: "paused", label: "Paused", accent: "text-orange-600" },
];

/**
 * Job board lifecycle counts (all postings — not scoped by candidate filter).
 */
export function JobStatusSummaryCards({ counts }: JobStatusSummaryCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <Card key={item.key} className="!p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
            {item.label}
          </p>
          <p
            className={`mt-2 text-3xl font-semibold tabular-nums tracking-tight ${item.accent}`}
          >
            {counts[item.key].toLocaleString()}
          </p>
        </Card>
      ))}
    </div>
  );
}
