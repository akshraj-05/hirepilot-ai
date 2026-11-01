import { Card } from "@/components/ui/Card";
import type { AIInsight } from "@/utils/api";

type StatsRow = {
  total: number;
  shortlisted: number;
  rejected: number;
  review: number;
};

type AIInsightsPanelProps = {
  insights: AIInsight[];
  stats: StatsRow;
  candidateCount: number;
};

export function AIInsightsPanel({ insights, stats, candidateCount }: AIInsightsPanelProps) {
  const skillGaps = insights.filter((i) => i.category === "skill_gap");
  const strategicNotes = insights.filter((i) => i.category === "strategic_note");

  const pct = stats.total > 0 ? Math.round((stats.shortlisted / stats.total) * 100) : 0;
  const summaryBullets =
    stats.total === 0
      ? ["Upload resumes and run analysis to see insights."]
      : [
          `${stats.total} candidate${stats.total !== 1 ? "s" : ""} in the pipeline.`,
          `${pct}% shortlisted by AI — ${stats.review} in review.`,
          stats.rejected > 0
            ? `${stats.rejected} rejected — review to confirm AI decisions.`
            : "No rejections yet.",
        ];

  return (
    <Card
      title="AI insights"
      description="Patterns across resumes and decisions — not just automation."
    >
      {candidateCount === 0 ? (
        <p className="text-sm text-[var(--hp-text-muted)]">
          Select a job with candidates or choose &quot;All jobs&quot; to see insights.
        </p>
      ) : (
        <div className="space-y-5">
          {/* Skill gaps from ai_insights table */}
          {skillGaps.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                Skill gaps
              </h3>
              <ul className="mt-2 space-y-1.5">
                {skillGaps.slice(0, 3).map((item) => (
                  <li
                    key={item.id}
                    className="flex items-start gap-2 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface)] px-3 py-1.5 text-sm text-[var(--hp-text)]"
                  >
                    <span className="mt-0.5 text-[var(--hp-accent)]">▸</span>
                    <span>
                      {item.skill_name && <strong>{item.skill_name}: </strong>}
                      {item.insight}
                    </span>
                  </li>
                ))}
                {skillGaps.length > 3 && (
                  <li className="px-3 text-xs text-[var(--hp-text-muted)]">
                    +{skillGaps.length - 3} more skill gaps
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Strategic notes from ai_insights table */}
          {strategicNotes.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                Strategic notes
              </h3>
              <ul className="mt-2 space-y-1.5">
                {strategicNotes.slice(0, 2).map((item) => (
                  <li
                    key={item.id}
                    className="flex items-start gap-2 rounded-lg border border-[var(--hp-border)] bg-blue-50/50 px-3 py-1.5 text-sm text-[var(--hp-text)]"
                  >
                    <span className="mt-0.5 text-blue-500">▸</span>
                    <span className="line-clamp-2">{item.insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pipeline summary (always shown) */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
              Pipeline summary
            </h3>
            <ul className="mt-2 list-inside list-disc space-y-2 text-sm text-[var(--hp-text-muted)]">
              {summaryBullets.map((line) => (
                <li key={line} className="leading-relaxed">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </Card>
  );
}
