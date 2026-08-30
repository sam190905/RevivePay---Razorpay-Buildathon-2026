"""SQLAlchemy model for RecoveryCase."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RecoveryCase(Base):
    """A recovery case created when a payment fails."""

    __tablename__ = "recovery_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True
    )
    amount_at_risk: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Amount in paise"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery_probability: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="0.0 to 1.0"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, default="open"
    )
    recommended_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actual_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recovered_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Amount in paise"
    )
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    payment: Mapped["Payment"] = relationship(back_populates="recovery_case")  # noqa: F821
    customer: Mapped["Customer"] = relationship(  # noqa: F821
        back_populates="recovery_cases"
    )
    recovery_actions: Mapped[list["RecoveryAction"]] = relationship(  # noqa: F821
        back_populates="recovery_case", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        back_populates="recovery_case", cascade="all, delete-orphan"
    )
