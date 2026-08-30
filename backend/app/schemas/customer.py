"""Pydantic schemas for Customer."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CustomerBase(BaseModel):
    """Shared customer fields."""

    external_customer_id: str
    name: str
    email: str | None = None
    phone: str | None = None


class CustomerCreate(CustomerBase):
    """Fields required to create a customer."""

    pass


class CustomerRead(CustomerBase):
    """Customer response schema."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
