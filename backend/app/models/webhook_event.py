"""WebhookEvent model for idempotency."""

import uuid
from datetime import datetime

from sqlalchemy import String, JSON, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class WebhookEvent(Base):
    """Tracks processed webhooks to ensure idempotency."""

    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # Razorpay event ID (e.g., evnt_xxx)
    razorpay_event_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    
    # Event type (e.g., payment.failed)
    event_type: Mapped[str] = mapped_column(String, index=True)
    
    # Full payload for audit/debugging
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
