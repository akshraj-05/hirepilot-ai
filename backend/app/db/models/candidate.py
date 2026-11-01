import uuid
from datetime import datetime

from sqlalchemy import ARRAY, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    mobile_number: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    years_experience: Mapped[int | None] = mapped_column(SmallInteger)
    experience_summary: Mapped[str | None] = mapped_column(Text)
    project_summary: Mapped[str | None] = mapped_column(Text)
    work_summary: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    red_flags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    green_flags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    # Sourcing fields
    source_channel: Mapped[str] = mapped_column(String(50), nullable=False, server_default="manual")  # manual, sourced
    source_platform: Mapped[str | None] = mapped_column(String(50))  # naukri, linkedin, indeed
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
