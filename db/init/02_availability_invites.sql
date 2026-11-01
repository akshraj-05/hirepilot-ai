-- Invitation links: candidate opens URL and selects one offered slot (availability only).

CREATE TABLE IF NOT EXISTS availability_invites (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id         UUID         NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    candidate_id   UUID         NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    posted_job_id  VARCHAR(20)  NOT NULL REFERENCES job_postings(job_id) ON DELETE CASCADE,
    token          UUID         NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    proposed_slots JSONB        NOT NULL,
    status         VARCHAR(20)  NOT NULL DEFAULT 'open',
    selected_slot  TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_availability_invites_token ON availability_invites (token);
