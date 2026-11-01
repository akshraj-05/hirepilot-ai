/**
 * API utility — all calls to the HirePilot backend go through here.
 *
 * Backend runs on http://localhost:4000 by default.
 * Set NEXT_PUBLIC_API_URL in .env.local to override.
 */

import { getOrgId } from "@/utils/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

// ─── Auth ───────────────────────────────────────────────────────────────────

export async function loginUser(email: string, password: string) {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail ?? "Login failed");
  }
  return res.json() as Promise<{
    id: string;
    email: string;
    name: string | null;
    role: string | null;
    organization_id: string;
  }>;
}

export async function signupUser(email: string, password: string, name?: string) {
  const res = await fetch(`${BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Signup failed" }));
    throw new Error(err.detail ?? "Signup failed");
  }
  return res.json() as Promise<{
    id: string;
    email: string;
    name: string | null;
    role: string | null;
    organization_id: string;
  }>;
}

// ─── Jobs ───────────────────────────────────────────────────────────────────

export async function createJob(title: string, description: string) {
  const res = await fetch(`${BASE_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description, organization_id: getOrgId() }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ job_id: string }>;
}

export async function listJobs() {
  const res = await fetch(
    `${BASE_URL}/api/jobs?organization_id=${getOrgId()}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<
    { job_id: string; title: string; job_description: string; status: string; date_posted: string }[]
  >;
}

export async function updateJobStatus(jobId: string, status: string) {
  const res = await fetch(`${BASE_URL}/api/jobs/${jobId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status, organization_id: getOrgId() }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ job_id: string; status: string }>;
}

export async function getJob(jobId: string) {
  const res = await fetch(
    `${BASE_URL}/api/jobs/${jobId}?organization_id=${getOrgId()}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    job_id: string;
    title: string;
    description: string;
  }>;
}

// ─── Candidates ──────────────────────────────────────────────────────────────

export async function uploadResume(file: File, candidateName: string, jobId: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("job_id", jobId);
  form.append("organization_id", getOrgId());
  if (candidateName) form.append("candidate_name", candidateName);
  const res = await fetch(`${BASE_URL}/api/candidates/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ candidate_id: string; message: string }>;
}

export async function listCandidates(jobId: string) {
  const res = await fetch(
    `${BASE_URL}/api/candidates?organization_id=${getOrgId()}&job_id=${jobId}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<
    { id: string; name: string; score: number; status: string; phone_number: string; summary: string }[]
  >;
}

export async function getCandidate(candidateId: string, jobId?: string) {
  const params = new URLSearchParams({ organization_id: getOrgId() });
  if (jobId) params.set("job_id", jobId);
  const res = await fetch(
    `${BASE_URL}/api/candidates/${candidateId}?${params}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    id: string;
    name: string;
    skills: string[];
    score: number;
    status: string;
    matched_skills: string[];
    missing_skills: string[];
    summary: string;
    project_summary: string | null;
    work_summary: string | null;
    red_flags: string[];
    green_flags: string[];
  }>;
}

export async function updateCandidateStatus(
  candidateId: string,
  jobId: string,
  status: string
) {
  const params = new URLSearchParams({
    organization_id: getOrgId(),
    job_id: jobId,
  });
  const res = await fetch(
    `${BASE_URL}/api/candidates/${candidateId}/status?${params}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ message: string }>;
}

// ─── Orchestrator (Analyze → Decision → Insights) ──────────────────────────

export async function runOrchestrator(
  candidateId: string,
  jobId: string
) {
  const res = await fetch(`${BASE_URL}/api/orchestrator`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_id: candidateId,
      job_id: jobId,
      organization_id: getOrgId(),
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    job_id: string;
    candidates: string[];
    resume_analyzer: { status: string; analyzed_candidates: string[] };
    decision_maker: { status: string; decisions: string[] };
    insight_agent: { status: string; insights: string[] };
  }>;
}

// ─── Feedback ────────────────────────────────────────────────────────────────

export async function submitFeedback(
  candidateId: string,
  jobId: string,
  decisionCorrect: boolean,
  comments = ""
) {
  const res = await fetch(`${BASE_URL}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_id: candidateId,
      job_id: jobId,
      organization_id: getOrgId(),
      decision_correct: decisionCorrect,
      comments,
    }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ message: string }>;
}

// ─── Meetings ───────────────────────────────────────────────────────────────

export async function listMeetings() {
  const res = await fetch(
    `${BASE_URL}/api/meetings?organization_id=${getOrgId()}`
  );
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<
    {
      id: string;
      org_id: string;
      candidate_id: string;
      posted_job_id: string;
      title: string;
      meeting_type: string;
      status: string;
      scheduled_at: string;
      duration_mins: number;
      meeting_link?: string;
      location?: string;
      interviewer_name: string;
      interviewer_email: string;
      notes?: string;
      created_at: string;
      updated_at: string;
    }[]
  >;
}

export async function createMeeting(body: {
  candidate_id: string;
  posted_job_id: string;
  title: string;
  meeting_type: string;
  scheduled_at: string;
  duration_mins?: number;
  interviewer_name: string;
  interviewer_email: string;
  meeting_link?: string;
  location?: string;
  notes?: string;
}) {
  const res = await fetch(`${BASE_URL}/api/meetings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...body, organization_id: getOrgId() }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteMeeting(meetingId: string) {
  const res = await fetch(`${BASE_URL}/api/meetings/${meetingId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ message: string }>;
}

/** Return all candidates with active invites, including tokens and status. */
export async function listInvitedCandidates() {
  const res = await fetch(`${BASE_URL}/api/scheduling/invites/invited-candidates`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    invites: { candidate_id: string; token: string; status: string }[];
  }>;
}

/** Check if candidate already has an active scheduling invite.
 *  Pass jobId to scope the check to a specific job so that an invite
 *  for Job A does not block scheduling for Job B.
 */
export async function checkCandidateInvite(candidateId: string, jobId?: string) {
  const params = new URLSearchParams({ candidate_id: candidateId });
  if (jobId) params.set("posted_job_id", jobId);
  const res = await fetch(`${BASE_URL}/api/scheduling/invites/check?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ has_invite: boolean; status?: string; token?: string }>;
}

/** Create invitation URL for candidate availability (dashboard). */
export async function createAvailabilityInvite(body: {
  candidate_id: string;
  posted_job_id: string;
  proposed_slots: string[];
}) {
  const res = await fetch(`${BASE_URL}/api/scheduling/invites`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ token: string; path: string }>;
}

/** Public: load invite (candidate page). */
export async function getAvailabilityInvite(token: string) {
  const res = await fetch(`${BASE_URL}/api/scheduling/invites/${token}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    status: string;
    proposed_slots: string[];
    job_title: string;
    candidate_name: string;
    selected_slot?: string;
  }>;
}

/** Public: candidate selects one slot. Backend creates a Google Calendar event + meeting. */
export async function chooseAvailabilitySlot(token: string, selected_slot: string) {
  const res = await fetch(`${BASE_URL}/api/scheduling/invites/${token}/choose`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selected_slot }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    message: string;
    selected_slot: string;
    meeting_link?: string;
    calendar_event_id?: string;
    meeting_id?: string;
  }>;
}

// ─── Google OAuth ────────────────────────────────────────────────────────────

export async function getGoogleAuthStatus() {
  const res = await fetch(`${BASE_URL}/api/google/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ connected: boolean; email: string | null }>;
}

export async function getGoogleAuthUrl() {
  const res = await fetch(`${BASE_URL}/api/google/auth-url`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ auth_url: string }>;
}

/** Send the scheduling link to the candidate's email via Gmail. */
export async function sendSchedulingEmail(token: string) {
  const res = await fetch(`${BASE_URL}/api/scheduling/invites/${token}/send-email`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{ message: string }>;
}

// ─── Dashboard ───────────────────────────────────────────────────────────────

export async function getDashboardStats(jobId: string) {
  const params = new URLSearchParams({
    organization_id: getOrgId(),
    job_id: jobId,
  });
  const res = await fetch(`${BASE_URL}/api/dashboard?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    total: number;
    shortlisted: number;
    rejected: number;
    review: number;
  }>;
}

export type AIInsight = {
  id: string;
  category: "skill_gap" | "strategic_note";
  insight: string;
  recommendation: string;
  skill_name: string | null;
  affected_count: number | null;
  posted_job_id: string | null;
};

export async function getRecentActivity(): Promise<{ id: string; message: string; time_label: string; status: string }[]> {
  const params = new URLSearchParams({ organization_id: getOrgId() });
  const res = await fetch(`${BASE_URL}/api/dashboard/activity?${params}`);
  if (!res.ok) return [];
  return res.json();
}

export async function getAIInsights(jobId?: string): Promise<AIInsight[]> {
  const params = new URLSearchParams({ organization_id: getOrgId() });
  if (jobId && jobId !== "all") params.set("job_id", jobId);
  const res = await fetch(`${BASE_URL}/api/dashboard/insights?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type JobSummary = {
  top_candidates: { id: string; name: string; score: number; status: string }[];
  missing_skills: { skill: string; count: number }[];
  score_distribution: { band: string; count: number }[];
};

export async function getJobSummary(jobId: string): Promise<JobSummary> {
  const params = new URLSearchParams({ organization_id: getOrgId(), job_id: jobId });
  const res = await fetch(`${BASE_URL}/api/dashboard/job-summary?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ─── Integrations ────────────────────────────────────────────────────────────

export async function listIntegrations() {
  const res = await fetch(`${BASE_URL}/api/integrations?org_id=${getOrgId()}`);
  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.integrations || [];
}

export async function testNaukriConnection(credentials: {
  client_id: string;
  client_secret: string;
}) {
  const res = await fetch(`${BASE_URL}/api/integrations/naukri/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      org_id: getOrgId(),
      credentials,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: "Connection test failed" }));
    throw new Error(error.error || "Connection test failed");
  }
  return res.json() as Promise<{
    success: boolean;
    platform: string;
    message: string;
    error?: string;
  }>;
}

export async function connectNaukri(credentials: {
  client_id: string;
  client_secret: string;
}) {
  const res = await fetch(`${BASE_URL}/api/integrations/naukri/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      org_id: getOrgId(),
      credentials,
    }),
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Failed to connect" }));
    throw new Error(error.detail || error.error || "Failed to connect");
  }
  return res.json() as Promise<{
    id: string;
    platform: string;
    is_active: boolean;
    connection_status: string;
    created_at: string;
  }>;
}

export async function syncNaukriCandidates(jobId: string, keywords: string) {
  const orgId = getOrgId();
  const res = await fetch(`${BASE_URL}/api/integrations/naukri/sync?org_id=${orgId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      job_id: jobId,
      filters: {
        keywords: keywords || "",
        location: null,
        experience_min_years: null,
        experience_max_years: null,
        skills: null,
      },
      limit: 50,
    }),
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || "Sync failed");
  }
  return res.json() as Promise<{
    sync_log_id: string;
    status: string;
    message: string;
  }>;
}

export async function disconnectIntegration(integrationId: string) {
  const res = await fetch(`${BASE_URL}/api/integrations/${integrationId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<{
    success: boolean;
    message: string;
  }>;
}
