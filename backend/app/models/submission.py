from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UpdateTimestampMixin


class Submission(Base, UpdateTimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    student_label: Mapped[str] = mapped_column(String(255), nullable=False)
    student_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="submissions")
    chunks: Mapped[list["SubmissionChunk"]] = relationship("SubmissionChunk", back_populates="submission", cascade="all, delete-orphan")
    relevance_results: Mapped[list["RelevanceResult"]] = relationship("RelevanceResult", back_populates="submission", cascade="all, delete-orphan")
    grading_result: Mapped["GradingResult | None"] = relationship("GradingResult", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    code_analyses: Mapped[list["CodeAnalysisResult"]] = relationship("CodeAnalysisResult", back_populates="submission", cascade="all, delete-orphan")
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship("ProcessingJob", back_populates="submission", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("evaluation_id", "file_hash", name="uq_evaluation_file_hash"),
        Index("idx_submissions_evaluation", "evaluation_id"),
        Index("idx_submissions_hash", "file_hash"),
        Index("idx_submissions_status", "extraction_status"),
    )
