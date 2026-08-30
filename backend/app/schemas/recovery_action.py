"""Pydantic schemas for RecoveryAction."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class RecoveryActionBase(BaseModel):
    """Shared recovery action fields."""

    action_type: str
    status: str = "pending"
    amount: int | None = None
    result: str | None = None
    error: str | None = None


class RecoveryActionCreate(RecoveryActionBase):
    """Fields required to create a recovery action."""

    recovery_case_id: uuid.UUID


class RecoveryActionRead(RecoveryActionBase):
    """Recovery action response schema."""

    id: uuid.UUID
    recovery_case_id: uuid.UUID
    requested_at: datetime
    executed_at: datetime | None = None

    model_config = {"from_attributes": True}
