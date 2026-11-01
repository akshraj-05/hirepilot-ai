import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class IntegrationSyncLog(Base):
    """Tracks every sync attempt for monitoring, debugging, and retry logic"""

    __tablename__ = "integration_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    integration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(20), ForeignKey("job_postings.job_id", ondelete="CASCADE"), nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)

    # Sync timing
    sync_started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    sync_completed_at: Mapped[datetime | None]

    # Sync status: pending, in_progress, completed, failed, partial
    sync_status: Mapped[str | None] = mapped_column(String(50))

    # Results
    total_candidates_fetched: Mapped[int] = mapped_column(default=0)
    candidates_processed: Mapped[int] = mapped_column(default=0)
    candidates_failed: Mapped[int] = mapped_column(default=0)
    candidates_deduplicated: Mapped[int] = mapped_column(default=0)  # Already existed in DB

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    error_type: Mapped[str | None] = mapped_column(String(100))  # e.g., INVALID_CREDENTIALS, RATE_LIMIT, NETWORK_ERROR

    # Retry logic
    retry_count: Mapped[int] = mapped_column(default=0)
    max_retries: Mapped[int] = mapped_column(default=3)
    next_retry_at: Mapped[datetime | None]

    # Debug info
    request_payload: Mapped[dict | None] = mapped_column(JSONB)
    response_summary: Mapped[dict | None] = mapped_column(JSONB)

    # Audit
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<IntegrationSyncLog(id={self.id}, job_id={self.job_id}, status={self.sync_status}, processed={self.candidates_processed})>"
