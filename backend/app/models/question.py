from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Integer, Text, String, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_concepts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    citation_policy: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="questions")
    rubric_criteria: Mapped[list["RubricCriterion"]] = relationship("RubricCriterion", back_populates="question", cascade="all, delete-orphan")
    relevance_results: Mapped[list["RelevanceResult"]] = relationship("RelevanceResult", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("evaluation_id", "order", name="uq_evaluation_question_order"),
        Index("idx_questions_eval_order", "evaluation_id", "order"),
    )
