from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Integer, JSON, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UpdateTimestampMixin


class ProcessingJob(Base, UpdateTimestampMixin):
    __tablename__ = "processing_jobs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evaluation_id: Mapped[UUID | None] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=True)
    submission_id: Mapped[UUID | None] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    evaluation: Mapped["Evaluation | None"] = relationship("Evaluation", back_populates="processing_jobs")
    submission: Mapped["Submission | None"] = relationship("Submission", back_populates="processing_jobs")

    __table_args__ = (
        Index("idx_processing_jobs_status_time", "status", "created_at"),
        Index("idx_processing_jobs_eval_type_status", "evaluation_id", "job_type", "status"),
    )
