import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

MeetingStatus = Enum(
    "scheduled", "completed", "cancelled", "no_show",
    name="meeting_status",
    create_type=False,
)

MeetingType = Enum(
    "screening", "technical", "behavioral", "culture_fit", "final",
    name="meeting_type",
    create_type=False,
)


class ScheduledMeeting(Base):
    __tablename__ = "scheduled_meetings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    posted_job_id: Mapped[str] = mapped_column(String(20), ForeignKey("job_postings.job_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    meeting_type: Mapped[str | None] = mapped_column(MeetingType)
    status: Mapped[str] = mapped_column(MeetingStatus, nullable=False, server_default="scheduled")
    scheduled_at: Mapped[datetime | None]
    duration_mins: Mapped[int | None] = mapped_column(SmallInteger, server_default="30")
    meeting_link: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(255))
    interviewer_name: Mapped[str | None] = mapped_column(String(255))
    interviewer_email: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
