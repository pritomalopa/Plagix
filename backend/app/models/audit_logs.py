from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID] = mapped_column(nullable=False)
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    request_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="audit_logs")
    actor: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_logs_tenant_time", "tenant_id", "created_at"),
        Index("idx_audit_logs_actor_time", "actor_id", "created_at"),
        Index("idx_audit_logs_target", "target_type", "target_id"),
    )
