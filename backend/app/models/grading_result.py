from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import JSON, Float, String, Text, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class GradingResult(Base):
    __tablename__ = "grading_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False)
    criterion_scores: Mapped[dict] = mapped_column(JSON, nullable=False)
    suggested_total: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    teacher_final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="grading_result")
    approver: Mapped["User | None"] = relationship("User", back_populates="grades_approved")

    __table_args__ = (
        Index("idx_grading_results_status", "status"),
    )
