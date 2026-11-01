-- =============================================================
-- HirePilot Database Schema
-- =============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================
-- ENUM TYPES
-- =============================================================

CREATE TYPE job_posting_status AS ENUM ('open', 'closed', 'draft', 'paused');
CREATE TYPE candidate_status    AS ENUM ('shortlist', 'review', 'reject');
CREATE TYPE insight_category    AS ENUM ('skill_gap', 'strategic_note');
CREATE TYPE meeting_status      AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');
CREATE TYPE meeting_type        AS ENUM ('screening', 'technical', 'behavioral', 'culture_fit', 'final');
CREATE TYPE resume_processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- =============================================================
-- TABLES (ordered by FK dependency)
-- =============================================================

-- 1. organization — no dependencies
CREATE TABLE organization (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name       VARCHAR(255) NOT NULL,
    slug       VARCHAR(100) UNIQUE NOT NULL,
    domain     VARCHAR(255),
    logo_url   TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. job_postings — depends on: organization
CREATE TABLE job_postings (
    job_id          VARCHAR(20)        PRIMARY KEY,
    organization_id UUID               REFERENCES organization(id) ON DELETE CASCADE,
    role            VARCHAR(255),
    description     TEXT,
    date_posted     DATE,
    status          job_posting_status,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_postings_status          ON job_postings (status);
CREATE INDEX idx_job_postings_date_posted     ON job_postings (date_posted);
CREATE INDEX idx_job_postings_organization_id ON job_postings (organization_id);

-- 3. candidates — depends on: organization
CREATE TABLE candidates (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id             UUID         NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name               VARCHAR(255),
    email              VARCHAR(255),
    mobile_number      VARCHAR(255),
    title              VARCHAR(255),
    years_experience   SMALLINT,
    experience_summary TEXT,
    skills             TEXT[],
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX        idx_candidates_org_id    ON candidates (org_id);
CREATE INDEX        idx_candidates_email     ON candidates (email);
CREATE UNIQUE INDEX idx_candidates_org_email ON candidates (org_id, email);

-- 4. users — depends on: organization
CREATE TABLE users (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID         NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT,
    name          VARCHAR(255),
    role          VARCHAR(50),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. decision_maker — depends on: organization, candidates, job_postings
CREATE TABLE decision_maker (
    id                         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                     UUID            NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    candidate_id               UUID            NOT NULL REFERENCES candidates(id)  ON DELETE CASCADE,
    posted_job_id              VARCHAR(20)     NOT NULL REFERENCES job_postings(job_id) ON DELETE CASCADE,
    match_score                NUMERIC(5, 2),
    skills_overlap_with_jd     TEXT[],
    skills_missing_from_resume TEXT[],
    status                     candidate_status,
    decision_reasons           TEXT[],
    override_status            candidate_status,
    ai_decision_correct        BOOLEAN,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX        idx_decision_maker_candidate_id  ON decision_maker (candidate_id);
CREATE INDEX        idx_decision_maker_posted_job_id ON decision_maker (posted_job_id);
CREATE INDEX        idx_decision_maker_status        ON decision_maker (status);
CREATE INDEX        idx_decision_maker_match_score   ON decision_maker (match_score DESC);
CREATE INDEX        idx_decision_maker_org_id        ON decision_maker (org_id);
CREATE UNIQUE INDEX idx_decision_maker_candidate_job ON decision_maker (candidate_id, posted_job_id);

-- 6. uploaded_resumes — depends on: organization, job_postings, candidates
CREATE TABLE uploaded_resumes (
    id                 UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id             UUID                     NOT NULL REFERENCES organization(id)      ON DELETE CASCADE,
    posted_job_id      VARCHAR(20)              NOT NULL REFERENCES job_postings(job_id)  ON DELETE CASCADE,
    candidate_id       UUID                     REFERENCES candidates(id)                 ON DELETE SET NULL,
    original_filename  VARCHAR(255),
    parsed_resume_text TEXT,
    parsed_at          TIMESTAMPTZ,
    file_path          TEXT,
    file_size_bytes    INTEGER,
    processing_status  resume_processing_status NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    uploaded_by        VARCHAR(255),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_resumes_posted_job_id           ON uploaded_resumes (posted_job_id);
CREATE INDEX idx_resumes_processing_status       ON uploaded_resumes (processing_status);
CREATE INDEX idx_uploaded_resumes_organization_id ON uploaded_resumes (org_id);

-- 7. ai_insights — depends on: organization, job_postings
CREATE TABLE ai_insights (
    id             UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id         UUID             NOT NULL REFERENCES organization(id)     ON DELETE CASCADE,
    posted_job_id  VARCHAR(20)      REFERENCES job_postings(job_id)          ON DELETE CASCADE,
    category       insight_category,
    skill_name     VARCHAR(100),
    affected_count SMALLINT,
    insight        TEXT,
    recommendation TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_insights_posted_job_id    ON ai_insights (posted_job_id);
CREATE INDEX idx_ai_insights_category         ON ai_insights (posted_job_id, category);
CREATE INDEX idx_ai_insights_organization_id  ON ai_insights (org_id);

-- 8. scheduled_meetings — depends on: organization, candidates, job_postings
CREATE TABLE scheduled_meetings (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id            UUID         NOT NULL REFERENCES organization(id)      ON DELETE CASCADE,
    candidate_id      UUID         NOT NULL REFERENCES candidates(id)        ON DELETE CASCADE,
    posted_job_id     VARCHAR(20)  NOT NULL REFERENCES job_postings(job_id)  ON DELETE CASCADE,
    title             VARCHAR(255),
    meeting_type      meeting_type,
    status            meeting_status NOT NULL DEFAULT 'scheduled',
    scheduled_at      TIMESTAMPTZ,
    duration_mins     SMALLINT     DEFAULT 30,
    meeting_link      TEXT,
    location          VARCHAR(255),
    interviewer_name  VARCHAR(255),
    interviewer_email VARCHAR(255),
    notes             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_meetings_candidate_id               ON scheduled_meetings (candidate_id);
CREATE INDEX idx_meetings_posted_job_id              ON scheduled_meetings (posted_job_id);
CREATE INDEX idx_meetings_scheduled_at               ON scheduled_meetings (scheduled_at);
CREATE INDEX idx_meetings_status                     ON scheduled_meetings (status);
CREATE INDEX idx_scheduled_meetings_organization_id  ON scheduled_meetings (org_id);

-- 9. activity_log — depends on: job_postings, candidates
CREATE TABLE activity_log (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    posted_job_id VARCHAR(20) REFERENCES job_postings(job_id) ON DELETE SET NULL,
    candidate_id  UUID        REFERENCES candidates(id)        ON DELETE SET NULL,
    actor         VARCHAR(255),
    action        VARCHAR(100),
    message       TEXT,
    metadata      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_log_created_at    ON activity_log (created_at DESC);
CREATE INDEX idx_activity_log_posted_job_id ON activity_log (posted_job_id);
