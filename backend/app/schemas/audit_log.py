"""Pydantic schemas for AuditLog."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogBase(BaseModel):
    """Shared audit log fields."""

    event_type: str
    actor: str = "system"
    action: str
    status: str
    metadata_json: dict[str, Any] | None = None


class AuditLogCreate(AuditLogBase):
    """Fields required to create an audit log entry."""

    recovery_case_id: uuid.UUID


class AuditLogRead(AuditLogBase):
    """Audit log response schema."""

    id: uuid.UUID
    recovery_case_id: uuid.UUID
    timestamp: datetime

    model_config = {"from_attributes": True}
