from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UpdateTimestampMixin


class Evaluation(Base, UpdateTimestampMixin):
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    max_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created")

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="evaluations")
    owner: Mapped["User"] = relationship("User", back_populates="evaluations_owned")
    questions: Mapped[list["Question"]] = relationship("Question", back_populates="evaluation", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="evaluation", cascade="all, delete-orphan")
    comparisons: Mapped[list["Comparison"]] = relationship("Comparison", back_populates="evaluation", cascade="all, delete-orphan")
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship("ProcessingJob", back_populates="evaluation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_evaluations_tenant_owner", "tenant_id", "owner_id"),
        Index("idx_evaluations_status", "status"),
    )
