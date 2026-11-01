import { Card } from "@/components/ui/Card";

type SkillsBreakdownProps = {
  matched: string[];
  missing: string[];
};

/**
 * Side-by-side chips for matched vs missing skills (vs JD).
 */
export function SkillsBreakdown({ matched, missing }: SkillsBreakdownProps) {
  return (
    <Card title="Skills breakdown" description="Against the job description.">
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--hp-shortlist)]">
            Matched
          </h3>
          <ul className="flex flex-wrap gap-2">
            {matched.map((s) => (
              <li
                key={s}
                className="rounded-md bg-[var(--hp-shortlist-bg)] px-2.5 py-1 text-sm text-[var(--hp-shortlist)]"
              >
                {s}
              </li>
            ))}
            {matched.length === 0 && (
              <li className="text-sm text-[var(--hp-text-muted)]">—</li>
            )}
          </ul>
        </div>
        <div>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[var(--hp-reject)]">
            Missing / gaps
          </h3>
          <ul className="flex flex-wrap gap-2">
            {missing.map((s) => (
              <li
                key={s}
                className="rounded-md bg-[var(--hp-reject-bg)] px-2.5 py-1 text-sm text-[var(--hp-reject)]"
              >
                {s}
              </li>
            ))}
            {missing.length === 0 && (
              <li className="text-sm text-[var(--hp-text-muted)]">
                No major gaps flagged
              </li>
            )}
          </ul>
        </div>
      </div>
    </Card>
  );
}
