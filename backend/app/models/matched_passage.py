from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Integer, Text, String, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class MatchedPassage(Base, TimestampMixin):
    __tablename__ = "matched_passages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    comparison_id: Mapped[UUID] = mapped_column(ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False)
    text_a_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_a_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_b_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_b_offset: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_a_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    text_b_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    match_type: Mapped[str] = mapped_column(String(50), nullable=False)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    comparison: Mapped["Comparison"] = relationship("Comparison", back_populates="matched_passages")

    __table_args__ = (
        Index("idx_matched_passages_comparison", "comparison_id"),
    )
