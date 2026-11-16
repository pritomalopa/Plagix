from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Float, JSON, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class CodeAnalysisResult(Base, TimestampMixin):
    __tablename__ = "code_analysis_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID | None] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    comparison_id: Mapped[UUID | None] = mapped_column(ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    token_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    ast_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_spans: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    parser_version: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationships
    submission: Mapped["Submission | None"] = relationship("Submission", back_populates="code_analyses")
    comparison: Mapped["Comparison | None"] = relationship("Comparison", back_populates="code_analyses")

    __table_args__ = (
        CheckConstraint(
            "(submission_id IS NOT NULL) OR (comparison_id IS NOT NULL)",
            name="check_code_analysis_target"
        ),
        Index("idx_code_analysis_submission", "submission_id"),
        Index("idx_code_analysis_comparison", "comparison_id"),
    )
