import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

CandidateStatus = Enum(
    "shortlist", "review", "reject",
    name="candidate_status",
    create_type=False,
)


class DecisionMaker(Base):
    __tablename__ = "decision_maker"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    posted_job_id: Mapped[str] = mapped_column(String(20), ForeignKey("job_postings.job_id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    skills_overlap_with_jd: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    skills_missing_from_resume: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    status: Mapped[str | None] = mapped_column(CandidateStatus)
    decision_reasons: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    override_status: Mapped[str | None] = mapped_column(CandidateStatus)
    ai_decision_correct: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
