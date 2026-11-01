"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { TopBar } from "@/components/layout/TopBar";
import { getAIInsights, getDashboardStats, getJobSummary, type AIInsight, type JobSummary } from "@/utils/api";

type Stats = { total: number; shortlisted: number; rejected: number; review: number };

export default function JobInsightsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [summary, setSummary] = useState<JobSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;
    Promise.all([
      getAIInsights(jobId).catch(() => [] as AIInsight[]),
      getDashboardStats(jobId).catch(() => null),
      getJobSummary(jobId).catch(() => null),
    ]).then(([ins, st, sum]) => {
      setInsights(ins);
      setStats(st);
      setSummary(sum);
    }).finally(() => setLoading(false));
  }, [jobId]);

  const skillGaps = insights.filter((i) => i.category === "skill_gap");
  const strategicNotes = insights.filter((i) => i.category === "strategic_note");

  const maxDistCount = summary
    ? Math.max(...summary.score_distribution.map((b) => b.count), 1)
    : 1;

  const bandColors: Record<string, string> = {
    "0-40": "bg-red-500",
    "40-60": "bg-yellow-500",
    "60-80": "bg-blue-500",
    "80-100": "bg-green-500",
  };

  return (
    <>
      <TopBar
        title="Job Insights"
        subtitle={`AI-generated insights for job ${jobId}`}
        actions={
          <div className="flex items-center gap-2 hp-no-print">
            <Link
              href="/jobs"
              className="inline-flex items-center gap-1 rounded-lg border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-4 py-2 text-sm font-medium text-[var(--hp-text)] hover:bg-[var(--hp-surface)] transition-colors"
            >
              ← Back to Jobs
            </Link>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 rounded-lg bg-[var(--hp-accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
            >
              ↓ Download Report
            </button>
          </div>
        }
      />

      {loading ? (
        <p className="text-sm text-[var(--hp-text-muted)]">Loading insights…</p>
      ) : !stats && !summary && insights.length === 0 ? (
        <p className="text-sm text-[var(--hp-text-muted)]">
          No insights available for this job yet. Upload and analyze resumes first.
        </p>
      ) : (
        <div className="space-y-6">

          {/* Pipeline stats */}
          {stats && (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {[
                { label: "Total candidates", value: stats.total },
                { label: "Shortlisted", value: stats.shortlisted, color: "text-green-400" },
                { label: "In review", value: stats.review, color: "text-yellow-400" },
                { label: "Rejected", value: stats.rejected, color: "text-red-400" },
              ].map(({ label, value, color }) => (
                <div
                  key={label}
                  className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-5 py-4"
                >
                  <p className="text-xs font-medium uppercase tracking-wide text-[var(--hp-text-muted)]">{label}</p>
                  <p className={`mt-1 text-3xl font-bold ${color ?? "text-[var(--hp-text)]"}`}>{value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Score distribution + Missing skills side by side */}
          {summary && (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

              {/* Score distribution */}
              <section className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-5 py-4">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                  Score distribution
                </h2>
                <div className="space-y-3">
                  {summary.score_distribution.map(({ band, count }) => (
                    <div key={band} className="flex items-center gap-3">
                      <span className="w-16 shrink-0 text-xs font-medium text-[var(--hp-text)]">{band}%</span>
                      <div className="flex-1 overflow-hidden rounded-full bg-[var(--hp-surface)] h-2.5">
                        <div
                          className={`h-2.5 rounded-full ${bandColors[band] ?? "bg-[var(--hp-accent)]"} transition-all`}
                          style={{ width: `${(count / maxDistCount) * 100}%` }}
                        />
                      </div>
                      <span className="w-6 shrink-0 text-right text-xs tabular-nums text-[var(--hp-text-muted)]">
                        {count}
                      </span>
                    </div>
                  ))}
                </div>
              </section>

              {/* Most common missing skills */}
              <section className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-5 py-4">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                  Most common missing skills
                </h2>
                {summary.missing_skills.length === 0 ? (
                  <p className="text-sm text-[var(--hp-text-muted)]">No missing skills data available.</p>
                ) : (
                  <div className="space-y-2">
                    {summary.missing_skills.map(({ skill, count }) => (
                      <div key={skill} className="flex items-center justify-between gap-3">
                        <span className="text-sm text-[var(--hp-text)]">{skill}</span>
                        <span className="shrink-0 rounded-full bg-[var(--hp-surface)] px-2 py-0.5 text-xs font-medium tabular-nums text-[var(--hp-text-muted)]">
                          {count} candidate{count !== 1 ? "s" : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          )}

          {/* Top candidates */}
          {summary && summary.top_candidates.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                Top shortlisted candidates
              </h2>
              <div className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] divide-y divide-[var(--hp-border)]">
                {summary.top_candidates.map((c, idx) => (
                  <div key={c.id} className="flex items-center gap-4 px-5 py-3">
                    <span className="w-5 shrink-0 text-xs font-bold tabular-nums text-[var(--hp-text-muted)]">
                      #{idx + 1}
                    </span>
                    <Link
                      href={`/candidates/${c.id}`}
                      className="flex-1 text-sm font-medium text-[var(--hp-text)] hover:text-[var(--hp-accent)] hover:underline"
                    >
                      {c.name}
                    </Link>
                    <span className="text-sm font-semibold tabular-nums text-green-400">
                      {c.score}%
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Skill gaps */}
          {skillGaps.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                Skill gaps ({skillGaps.length})
              </h2>
              <div className="space-y-3">
                {skillGaps.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-5 py-4"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        {item.skill_name && (
                          <p className="mb-1 text-sm font-semibold text-[var(--hp-text)]">
                            {item.skill_name}
                            {item.affected_count != null && (
                              <span className="ml-2 text-xs font-normal text-[var(--hp-text-muted)]">
                                {item.affected_count} candidate{item.affected_count !== 1 ? "s" : ""} affected
                              </span>
                            )}
                          </p>
                        )}
                        <p className="text-sm text-[var(--hp-text-muted)]">{item.insight}</p>
                      </div>
                      <span className="mt-0.5 shrink-0 text-[var(--hp-accent)]">▸</span>
                    </div>
                    {item.recommendation && (
                      <p className="mt-3 border-t border-[var(--hp-border)] pt-3 text-xs text-[var(--hp-text-muted)]">
                        <span className="font-medium text-[var(--hp-text)]">Recommendation: </span>
                        {item.recommendation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Strategic notes */}
          {strategicNotes.length > 0 && (
            <section>
              <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--hp-text-muted)]">
                Strategic notes ({strategicNotes.length})
              </h2>
              <div className="space-y-3">
                {strategicNotes.map((item) => (
                  <div
                    key={item.id}
                    className="rounded-[var(--hp-radius)] border border-[var(--hp-border)] bg-[var(--hp-surface-elevated)] px-5 py-4"
                  >
                    <p className="text-sm text-[var(--hp-text-muted)]">{item.insight}</p>
                    {item.recommendation && (
                      <p className="mt-3 border-t border-[var(--hp-border)] pt-3 text-xs text-[var(--hp-text-muted)]">
                        <span className="font-medium text-[var(--hp-text)]">Recommendation: </span>
                        {item.recommendation}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {insights.length === 0 && stats && (
            <p className="text-sm text-[var(--hp-text-muted)]">
              No AI insights generated for this job yet. Run the analysis pipeline to generate them.
            </p>
          )}
        </div>
      )}
    </>
  );
}
