import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

InsightCategory = Enum(
    "skill_gap", "strategic_note",
    name="insight_category",
    create_type=False,
)


class AIInsight(Base):
    __tablename__ = "ai_insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    posted_job_id: Mapped[str | None] = mapped_column(String(20), ForeignKey("job_postings.job_id", ondelete="CASCADE"))
    category: Mapped[str | None] = mapped_column(InsightCategory)
    skill_name: Mapped[str | None] = mapped_column(String(100))
    affected_count: Mapped[int | None] = mapped_column(SmallInteger)
    insight: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
