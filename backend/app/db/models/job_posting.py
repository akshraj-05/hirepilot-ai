import uuid
from datetime import date, datetime

from sqlalchemy import Date, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

# create_type=False — enum already exists in the DB via 01_schema.sql
JobPostingStatus = Enum(
    "open", "closed", "draft", "paused",
    name="job_posting_status",
    create_type=False,
)


class JobPosting(Base):
    __tablename__ = "job_postings"

    job_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"))
    role: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None]
    date_posted: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(JobPostingStatus)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
