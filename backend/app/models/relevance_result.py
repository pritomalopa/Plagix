from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Float, Text, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class RelevanceResult(Base, TimestampMixin):
    __tablename__ = "relevance_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="relevance_results")
    question: Mapped["Question"] = relationship("Question", back_populates="relevance_results")

    __table_args__ = (
        UniqueConstraint("submission_id", "question_id", name="uq_submission_question_relevance"),
        Index("idx_relevance_category", "category"),
    )
