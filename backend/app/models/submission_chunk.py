from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Integer, Text, String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class SubmissionChunk(Base, TimestampMixin):
    __tablename__ = "submission_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    paragraph: Mapped[int] = mapped_column(Integer, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, nullable=False)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship("Submission", back_populates="chunks")

    __table_args__ = (
        Index("idx_submission_chunks_sub_page", "submission_id", "page", "paragraph"),
    )
