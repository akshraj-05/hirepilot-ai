import type { JobPosting } from "./types";
import type { AIInsight, JobSummary } from "./api";
import { getDashboardStats, getJobSummary, getAIInsights } from "./api";

const STATUS_COLORS: Record<string, string> = {
  open: "#16a34a",
  closed: "#64748b",
  draft: "#ca8a04",
  paused: "#ea580c",
};

const STATUS_BG: Record<string, string> = {
  open: "#dcfce7",
  closed: "#f1f5f9",
  draft: "#fef9c3",
  paused: "#ffedd5",
};

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(new Date(iso + "T12:00:00"));
  } catch {
    return iso;
  }
}

// ─── Current View (simple jobs table) ────────────────────────────────────────

function jobRow(job: JobPosting) {
  const color = STATUS_COLORS[job.status] ?? "#64748b";
  const bg = STATUS_BG[job.status] ?? "#f1f5f9";
  return `
    <tr>
      <td style="padding:10px 14px;font-family:monospace;font-size:12px;font-weight:600;color:#0f172a;white-space:nowrap;border-bottom:1px solid #e2e8f0">${job.jobId}</td>
      <td style="padding:10px 14px;font-weight:500;color:#0f172a;border-bottom:1px solid #e2e8f0">${job.role}</td>
      <td style="padding:10px 14px;color:#475569;font-size:13px;border-bottom:1px solid #e2e8f0;max-width:320px">${job.description.slice(0, 200)}${job.description.length > 200 ? "…" : ""}</td>
      <td style="padding:10px 14px;white-space:nowrap;color:#0f172a;border-bottom:1px solid #e2e8f0">${formatDate(job.datePosted)}</td>
      <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0">
        <span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:11px;font-weight:600;background:${bg};color:${color}">
          ${job.status.charAt(0).toUpperCase() + job.status.slice(1)}
        </span>
      </td>
    </tr>`;
}

export function printJobsReport(jobs: JobPosting[], title: string) {
  const generated = new Intl.DateTimeFormat("en-US", {
    dateStyle: "long",
    timeStyle: "short",
  }).format(new Date());

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${title}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #fff; color: #0f172a; padding: 40px; }
    header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 28px; padding-bottom: 16px; border-bottom: 2px solid #2563eb; }
    header h1 { font-size: 22px; font-weight: 700; color: #0f172a; }
    header p { font-size: 12px; color: #64748b; margin-top: 4px; }
    .meta { text-align: right; font-size: 12px; color: #64748b; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    thead tr { background: #f8fafc; }
    thead th { padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
    footer { margin-top: 32px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center; }
    @media print { body { padding: 20px; } @page { margin: 1.5cm; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>HirePilot AI — ${title}</h1>
      <p>${jobs.length} job${jobs.length !== 1 ? "s" : ""} listed</p>
    </div>
    <div class="meta">Generated: ${generated}</div>
  </header>
  <table>
    <thead>
      <tr><th>Job ID</th><th>Role</th><th>Description</th><th>Date Posted</th><th>Status</th></tr>
    </thead>
    <tbody>${jobs.map(jobRow).join("")}</tbody>
  </table>
  <footer>HirePilot AI &nbsp;·&nbsp; Confidential &nbsp;·&nbsp; ${generated}</footer>
  <script>window.onload = () => { window.print(); }<\/script>
</body>
</html>`;

  openHtmlInWindow(html);
}

function openHtmlInWindow(html: string) {
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank");
  if (win) setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

// ─── All Jobs Insights Report ─────────────────────────────────────────────────

type JobInsightsData = {
  job: JobPosting;
  stats: { total: number; shortlisted: number; rejected: number; review: number } | null;
  summary: JobSummary | null;
  insights: AIInsight[];
};

function bandColor(band: string) {
  if (band === "0-40") return "#ef4444";
  if (band === "40-60") return "#eab308";
  if (band === "60-80") return "#3b82f6";
  return "#22c55e";
}

function renderJobInsights(data: JobInsightsData, index: number): string {
  const { job, stats, summary, insights } = data;
  const color = STATUS_COLORS[job.status] ?? "#64748b";
  const bg = STATUS_BG[job.status] ?? "#f1f5f9";
  const skillGaps = insights.filter((i) => i.category === "skill_gap");
  const strategicNotes = insights.filter((i) => i.category === "strategic_note");
  const maxCount = summary ? Math.max(...summary.score_distribution.map((b) => b.count), 1) : 1;

  return `
  <div style="break-before:${index === 0 ? "avoid" : "page"};padding-bottom:32px">
    <!-- Job header -->
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding-bottom:12px;border-bottom:2px solid #2563eb">
      <div>
        <span style="font-family:monospace;font-size:12px;font-weight:600;color:#64748b">${job.jobId}</span>
        <h2 style="font-size:18px;font-weight:700;color:#0f172a;margin-top:2px">${job.role}</h2>
        <p style="font-size:12px;color:#64748b;margin-top:2px">Posted ${formatDate(job.datePosted)}</p>
      </div>
      <span style="padding:4px 12px;border-radius:9999px;font-size:12px;font-weight:600;background:${bg};color:${color}">
        ${job.status.charAt(0).toUpperCase() + job.status.slice(1)}
      </span>
    </div>

    ${stats ? `
    <!-- Pipeline stats -->
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px">
      ${[
        { label: "Total", value: stats.total, color: "#0f172a" },
        { label: "Shortlisted", value: stats.shortlisted, color: "#16a34a" },
        { label: "In Review", value: stats.review, color: "#ca8a04" },
        { label: "Rejected", value: stats.rejected, color: "#dc2626" },
      ].map(({ label, value, color: c }) => `
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px">
          <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b">${label}</p>
          <p style="font-size:26px;font-weight:700;color:${c};margin-top:4px">${value}</p>
        </div>`).join("")}
    </div>` : ""}

    ${summary ? `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
      <!-- Score distribution -->
      <div style="border:1px solid #e2e8f0;border-radius:8px;padding:16px">
        <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:12px">Score Distribution</p>
        ${summary.score_distribution.map(({ band, count }) => `
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
            <span style="width:52px;font-size:11px;font-weight:600;color:#0f172a;flex-shrink:0">${band}%</span>
            <div style="flex:1;height:8px;background:#f1f5f9;border-radius:9999px;overflow:hidden">
              <div style="height:8px;width:${Math.round((count / maxCount) * 100)}%;background:${bandColor(band)};border-radius:9999px"></div>
            </div>
            <span style="width:20px;text-align:right;font-size:11px;color:#64748b;flex-shrink:0">${count}</span>
          </div>`).join("")}
      </div>

      <!-- Missing skills -->
      <div style="border:1px solid #e2e8f0;border-radius:8px;padding:16px">
        <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:12px">Most Common Missing Skills</p>
        ${summary.missing_skills.length === 0
          ? `<p style="font-size:12px;color:#94a3b8">No data available.</p>`
          : summary.missing_skills.map(({ skill, count }) => `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px">
              <span style="font-size:12px;color:#0f172a">${skill}</span>
              <span style="font-size:11px;font-weight:600;color:#64748b;background:#f1f5f9;padding:1px 8px;border-radius:9999px">${count}</span>
            </div>`).join("")}
      </div>
    </div>

    <!-- Top candidates -->
    ${summary.top_candidates.length > 0 ? `
    <div style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;margin-bottom:20px">
      <div style="padding:12px 16px;background:#f8fafc;border-bottom:1px solid #e2e8f0">
        <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b">Top Shortlisted Candidates</p>
      </div>
      ${summary.top_candidates.map((c, i) => `
        <div style="display:flex;align-items:center;gap:12px;padding:10px 16px;border-bottom:1px solid #f1f5f9">
          <span style="font-size:11px;font-weight:700;color:#94a3b8;width:20px">#${i + 1}</span>
          <span style="flex:1;font-size:13px;font-weight:500;color:#0f172a">${c.name}</span>
          <span style="font-size:13px;font-weight:700;color:#16a34a">${c.score}%</span>
        </div>`).join("")}
    </div>` : ""}` : ""}

    ${skillGaps.length > 0 ? `
    <!-- Skill gaps -->
    <div style="margin-bottom:20px">
      <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:8px">Skill Gaps (${skillGaps.length})</p>
      ${skillGaps.map((item) => `
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;margin-bottom:8px">
          ${item.skill_name ? `<p style="font-size:13px;font-weight:600;color:#0f172a;margin-bottom:4px">${item.skill_name}${item.affected_count != null ? ` <span style="font-weight:400;font-size:11px;color:#64748b">(${item.affected_count} candidate${item.affected_count !== 1 ? "s" : ""} affected)</span>` : ""}</p>` : ""}
          <p style="font-size:12px;color:#475569">${item.insight}</p>
          ${item.recommendation ? `<p style="font-size:11px;color:#64748b;margin-top:8px;padding-top:8px;border-top:1px solid #f1f5f9"><strong style="color:#0f172a">Recommendation: </strong>${item.recommendation}</p>` : ""}
        </div>`).join("")}
    </div>` : ""}

    ${strategicNotes.length > 0 ? `
    <!-- Strategic notes -->
    <div style="margin-bottom:20px">
      <p style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:8px">Strategic Notes (${strategicNotes.length})</p>
      ${strategicNotes.map((item) => `
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;margin-bottom:8px">
          <p style="font-size:12px;color:#475569">${item.insight}</p>
          ${item.recommendation ? `<p style="font-size:11px;color:#64748b;margin-top:8px;padding-top:8px;border-top:1px solid #f1f5f9"><strong style="color:#0f172a">Recommendation: </strong>${item.recommendation}</p>` : ""}
        </div>`).join("")}
    </div>` : ""}
  </div>`;
}

export async function printAllJobsInsightsReport(jobs: JobPosting[]) {
  const generated = new Intl.DateTimeFormat("en-US", {
    dateStyle: "long",
    timeStyle: "short",
  }).format(new Date());

  const results = await Promise.all(
    jobs.map(async (job) => {
      const [stats, summary, insights] = await Promise.all([
        getDashboardStats(job.jobId).catch(() => null),
        getJobSummary(job.jobId).catch(() => null),
        getAIInsights(job.jobId).catch(() => [] as AIInsight[]),
      ]);
      return { job, stats, summary, insights } as JobInsightsData;
    })
  );

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>All Jobs Insights Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #fff; color: #0f172a; padding: 40px; }
    footer { margin-top: 32px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center; }
    @media print { body { padding: 20px; } @page { margin: 1.5cm; } }
  </style>
</head>
<body>
  <!-- Cover header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:36px;padding-bottom:16px;border-bottom:3px solid #2563eb">
    <div>
      <h1 style="font-size:24px;font-weight:700;color:#0f172a">HirePilot AI — All Jobs Insights Report</h1>
      <p style="font-size:13px;color:#64748b;margin-top:4px">${jobs.length} job${jobs.length !== 1 ? "s" : ""} included</p>
    </div>
    <p style="font-size:12px;color:#64748b">Generated: ${generated}</p>
  </div>

  ${results.map((d, i) => renderJobInsights(d, i)).join("")}

  <footer>HirePilot AI &nbsp;·&nbsp; Confidential &nbsp;·&nbsp; ${generated}</footer>
  <script>window.onload = () => { window.print(); }<\/script>
</body>
</html>`;

  openHtmlInWindow(html);
}
