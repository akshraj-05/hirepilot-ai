import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

ResumeProcessingStatus = Enum(
    "pending", "processing", "completed", "failed",
    name="resume_processing_status",
    create_type=False,
)


class UploadedResume(Base):
    __tablename__ = "uploaded_resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    posted_job_id: Mapped[str] = mapped_column(String(20), ForeignKey("job_postings.job_id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="SET NULL"))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    parsed_resume_text: Mapped[str | None] = mapped_column(Text)
    parsed_at: Mapped[datetime | None]
    file_path: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    processing_status: Mapped[str] = mapped_column(ResumeProcessingStatus, nullable=False, server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    uploaded_by: Mapped[str | None] = mapped_column(String(255))
    # Sourcing fields
    is_sourced: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    source_type: Mapped[str | None] = mapped_column(String(50))  # naukri, linkedin, indeed
    external_candidate_id: Mapped[str | None] = mapped_column(String(255))  # ID from the external platform
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
