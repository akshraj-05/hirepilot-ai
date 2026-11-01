/**
 * Shared domain types for HirePilot AI (client-safe).
 *
 * TODO(mock-removal): Regenerate or import from the API schema (OpenAPI / zod)
 * when mock data is removed so types stay aligned with the backend.
 */

/** Hiring pipeline status — drives badge colors and filters */
export type CandidateStatus = "shortlist" | "reject" | "review";

/** Full candidate record for list + detail views */
export interface Candidate {
  id: string;
  /** HR job posting id, e.g. JOB-2026-014 — drives dashboard job filter */
  postedJobId: string;
  name: string;
  email: string;
  phone?: string;
  matchScore: number;
  status: CandidateStatus;
  title: string;
  yearsExperience: number;
  /** All skills parsed from resume */
  skills: string[];
  skillsOverlapWithJD: string[];
  skillsMissingFromResume: string[];
  experienceSummary: string;
  /** AI explainability bullets */
  decisionReasons: string[];
  /** Source channel: manual or sourced */
  source_channel?: string;
  /** Source platform: naukri, linkedin, indeed */
  source_platform?: string;
}

/** Dashboard “recent activity” row */
export interface ActivityItem {
  id: string;
  message: string;
  /** ISO-ish label for mock display */
  timeLabel: string;
  status?: CandidateStatus;
}

/** HR job posting lifecycle — drives filters and badges */
export type JobPostingStatus = "open" | "closed" | "draft" | "paused";

/** Job row for the jobs directory (mock / future API) */
export interface JobPosting {
  /** Display id shown to HR, e.g. JOB-2026-014 */
  jobId: string;
  /** Internal key for React lists */
  id: string;
  role: string;
  description: string;
  /** ISO date (YYYY-MM-DD) — date posted */
  datePosted: string;
  status: JobPostingStatus;
}

/** Interview format */
export type MeetingType =
  | "phone_screen"
  | "technical"
  | "hr_round"
  | "final"
  | "offer";

/** Lifecycle state of a scheduled meeting */
export type MeetingStatus =
  | "scheduled"
  | "completed"
  | "cancelled"
  | "rescheduled";

/** Scheduled interview / meeting record */
export interface Meeting {
  id: string;
  org_id: string;
  candidate_id: string;
  posted_job_id: string;
  title: string;
  meeting_type: MeetingType;
  status: MeetingStatus;
  /** ISO datetime string */
  scheduled_at: string;
  duration_mins: number;
  meeting_link?: string;
  location?: string;
  interviewer_name: string;
  interviewer_email: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}
