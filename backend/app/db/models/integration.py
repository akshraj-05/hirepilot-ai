import uuid
from datetime import datetime

from sqlalchemy import String, Text, Boolean, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Integration(Base):
    """Stores encrypted credentials for external platform integrations (Naukri, LinkedIn, Indeed)"""

    __tablename__ = "integrations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)

    # Platform identifier: 'naukri', 'linkedin', 'indeed'
    platform: Mapped[str] = mapped_column(String(50), nullable=False)

    # Encrypted credentials (JSON: {"username": "...", "password": "...", "api_key": "..."})
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)
    encryption_salt: Mapped[str | None] = mapped_column(String(255))

    # Connection status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    connection_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # pending, connected, failed, expired

    last_tested_at: Mapped[datetime | None]
    test_error_message: Mapped[str | None] = mapped_column(Text)

    # Sync metadata
    last_synced_at: Mapped[datetime | None]
    sync_status: Mapped[str | None] = mapped_column(String(50))  # idle, syncing, failed
    total_candidates_synced: Mapped[int] = mapped_column(default=0)

    # Audit
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    created_by: Mapped[str | None] = mapped_column(String(255))

    def __repr__(self):
        return f"<Integration(id={self.id}, platform={self.platform}, org_id={self.org_id}, is_active={self.is_active})>"
