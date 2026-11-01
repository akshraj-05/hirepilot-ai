import type { CandidateStatus } from "@/utils/types";

const statusStyles: Record<
  CandidateStatus,
  { label: string; className: string }
> = {
  shortlist: {
    label: "Shortlist",
    className:
      "bg-[var(--hp-shortlist-bg)] text-[var(--hp-shortlist)] ring-1 ring-inset ring-green-600/15",
  },
  reject: {
    label: "Reject",
    className:
      "bg-[var(--hp-reject-bg)] text-[var(--hp-reject)] ring-1 ring-inset ring-red-600/15",
  },
  review: {
    label: "Review",
    className:
      "bg-[var(--hp-review-bg)] text-[var(--hp-review)] ring-1 ring-inset ring-yellow-600/20",
  },
};

type BadgeProps = {
  status: CandidateStatus;
  className?: string;
};

/**
 * Status pill with HirePilot color coding (green / red / yellow).
 */
export function Badge({ status, className = "" }: BadgeProps) {
  const cfg = statusStyles[status];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.className} ${className}`}
    >
      {cfg.label}
    </span>
  );
}
