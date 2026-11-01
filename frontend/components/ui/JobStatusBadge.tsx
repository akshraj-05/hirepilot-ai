import type { JobPostingStatus } from "@/utils/types";

const styles: Record<
  JobPostingStatus,
  { label: string; className: string }
> = {
  open: {
    label: "Open",
    className:
      "bg-[var(--hp-shortlist-bg)] text-[var(--hp-shortlist)] ring-1 ring-inset ring-green-600/15",
  },
  closed: {
    label: "Closed",
    className:
      "bg-[var(--hp-surface)] text-[var(--hp-text-muted)] ring-1 ring-inset ring-[var(--hp-border)]",
  },
  draft: {
    label: "Draft",
    className:
      "bg-[var(--hp-review-bg)] text-[var(--hp-review)] ring-1 ring-inset ring-yellow-600/20",
  },
  paused: {
    label: "Paused",
    className:
      "bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-200",
  },
};

type JobStatusBadgeProps = {
  status: JobPostingStatus;
  className?: string;
};

/** Job posting lifecycle badge (distinct from candidate pipeline badges). */
export function JobStatusBadge({ status, className = "" }: JobStatusBadgeProps) {
  const cfg = styles[status];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.className} ${className}`}
    >
      {cfg.label}
    </span>
  );
}
