"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import type { Candidate } from "@/utils/types";
import { getScoreRangeBuckets, getStatusDistribution } from "@/utils/dashboard";

type CandidateDistributionChartsProps = {
  candidates: Candidate[];
};

const STATUS_COLORS: Record<string, string> = {
  Shortlisted: "#16a34a",
  "In review": "#ca8a04",
  Rejected: "#dc2626",
};

export function CandidateDistributionCharts({ candidates }: CandidateDistributionChartsProps) {
  const pieData = getStatusDistribution(candidates)
    .filter((d) => d.value > 0)
    .map((d) => ({ ...d, fill: STATUS_COLORS[d.name] ?? "#64748b" }));

  const barData = getScoreRangeBuckets(candidates);
  const empty = candidates.length === 0;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Status distribution" description="Shortlisted vs rejected vs in review.">
        {empty || pieData.length === 0 ? (
          <p className="py-12 text-center text-sm text-[var(--hp-text-muted)]">
            No candidates in this view.
          </p>
        ) : (
          <div className="w-full min-w-0">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={52}
                  outerRadius={88}
                  paddingAngle={2}
                />
                <Tooltip
                  formatter={(value) => [`${value ?? 0}`, "Candidates"]}
                  contentStyle={{ borderRadius: "8px", border: "1px solid var(--hp-border)" }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <Card title="Candidates by score range" description="Match score bands for the current filter.">
        {empty ? (
          <p className="py-12 text-center text-sm text-[var(--hp-text-muted)]">
            No candidates in this view.
          </p>
        ) : (
          <div className="w-full min-w-0">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="range"
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  axisLine={{ stroke: "#e2e8f0" }}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => [`${value ?? 0}`, "Count"]}
                  contentStyle={{ borderRadius: "8px", border: "1px solid var(--hp-border)" }}
                />
                <Bar dataKey="count" fill="#2563eb" radius={[6, 6, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
    </div>
  );
}
