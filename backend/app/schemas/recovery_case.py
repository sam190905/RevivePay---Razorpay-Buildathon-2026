"""Pydantic schemas for RecoveryCase."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class RecoveryCaseBase(BaseModel):
    """Shared recovery case fields."""

    amount_at_risk: int
    reason: str | None = None
    recovery_probability: float | None = None
    status: str = "open"
    recommended_action: str | None = None
    actual_action: str | None = None
    recovered_amount: int = 0


class RecoveryCaseCreate(RecoveryCaseBase):
    """Fields required to create a recovery case."""

    payment_id: uuid.UUID
    customer_id: uuid.UUID


class RecoveryCaseRead(RecoveryCaseBase):
    """Recovery case response schema."""

    id: uuid.UUID
    payment_id: uuid.UUID
    customer_id: uuid.UUID
    opened_at: datetime
    closed_at: datetime | None = None

    model_config = {"from_attributes": True}


class RecoveryCaseSummary(BaseModel):
    """Lightweight recovery case for list views."""

    id: uuid.UUID
    amount_at_risk: int
    status: str
    recovery_probability: float | None = None
    recommended_action: str | None = None
    recovered_amount: int
    opened_at: datetime

    model_config = {"from_attributes": True}
