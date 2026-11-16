from uuid import UUID, uuid4
from sqlalchemy import String, Integer, Text, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    criterion: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_points: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    expected_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="rubric_criteria")

    __table_args__ = (
        Index("idx_rubric_question_order", "question_id", "order"),
    )
