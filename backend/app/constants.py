"""Shared constants used across the app."""

import uuid

# Fixed demo organization — auto-created in the DB on startup.
# All API calls without auth belong to this org.
DEMO_ORG_UUID = uuid.UUID("00000000-0000-0000-0000-000000000025")
DEMO_ORG_SLUG = "demo-org"
