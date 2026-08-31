"""SQLAlchemy model for RecoveryAction."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RecoveryAction(Base):
    """An individual recovery action attempted for a case."""

    __tablename__ = "recovery_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    recovery_case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recovery_cases.id"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="e.g. create_payment_link, manual_review"
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )
    amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Amount in paise"
    )
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    recovery_case: Mapped["RecoveryCase"] = relationship(  # noqa: F821
        back_populates="recovery_actions"
    )
