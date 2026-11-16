from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Float, JSON, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UpdateTimestampMixin


class Comparison(Base, UpdateTimestampMixin):
    __tablename__ = "comparisons"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    submission_a_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    submission_b_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    exact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    lexical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="comparisons")
    submission_a: Mapped["Submission"] = relationship("Submission", foreign_keys=[submission_a_id])
    submission_b: Mapped["Submission"] = relationship("Submission", foreign_keys=[submission_b_id])
    matched_passages: Mapped[list["MatchedPassage"]] = relationship("MatchedPassage", back_populates="comparison", cascade="all, delete-orphan")
    code_analyses: Mapped[list["CodeAnalysisResult"]] = relationship("CodeAnalysisResult", back_populates="comparison", cascade="all, delete-orphan")

    __table_args__ = (
        # CRITICAL: Canonical pair constraint ensuring submission_a_id < submission_b_id
        CheckConstraint("submission_a_id < submission_b_id", name="check_canonical_pair"),
        # CRITICAL: Unique constraint over evaluation and canonical pair
        UniqueConstraint("evaluation_id", "submission_a_id", "submission_b_id", name="uq_evaluation_canonical_pair"),
        Index("idx_comparisons_eval_status", "evaluation_id", "status"),
    )
