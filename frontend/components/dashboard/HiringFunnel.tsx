import { Card } from "@/components/ui/Card";

export type FunnelStats = {
  total: number;
  shortlist: number;
  review: number;
  reject: number;
};

type HiringFunnelProps = {
  stats: FunnelStats;
};

/**
 * Pipeline visualization: total → shortlist → in review → rejected (counts + share of total).
 */
export function HiringFunnel({ stats }: HiringFunnelProps) {
  const base = Math.max(stats.total, 1);
  const stages: {
    label: string;
    count: number;
    barPct: number;
    hint: string;
  }[] = [
    {
      label: "Total candidates",
      count: stats.total,
      barPct: 100,
      hint: "All applicants in this view",
    },
    {
      label: "Shortlist",
      count: stats.shortlist,
      barPct: (stats.shortlist / base) * 100,
      hint: "% of pipeline",
    },
    {
      label: "In review",
      count: stats.review,
      barPct: (stats.review / base) * 100,
      hint: "% of pipeline",
    },
    {
      label: "Rejected",
      count: stats.reject,
      barPct: (stats.reject / base) * 100,
      hint: "% of pipeline",
    },
  ];

  return (
    <Card
      title="Hiring funnel"
      description="How candidates are distributed across outcomes for the selected job filter."
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stages.map((s, i) => (
          <div key={s.label} className="relative flex flex-col">
            {i > 0 && (
              <span
                className="absolute -left-2 top-8 hidden text-[var(--hp-text-muted)] lg:block"
                aria-hidden
              >
                →
              </span>
            )}
            <div className="rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">
                {s.label}
              </p>
              <p className="mt-1 text-2xl font-semibold tabular-nums text-[var(--hp-text)]">
                {s.count.toLocaleString()}
              </p>
              <p className="mt-0.5 text-xs text-[var(--hp-text-muted)]">{s.hint}</p>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-[var(--hp-border)]">
                <div
                  className="h-full rounded-full bg-[var(--hp-accent)] transition-all duration-500"
                  style={{ width: `${Math.min(100, s.barPct)}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
