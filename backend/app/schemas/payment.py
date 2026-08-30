"""Pydantic schemas for Payment."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class PaymentBase(BaseModel):
    """Shared payment fields."""

    razorpay_payment_id: str
    order_id: str | None = None
    amount: int
    currency: str = "INR"
    status: str = "failed"
    method: str | None = None
    failure_reason: str | None = None
    failure_code: str | None = None


class PaymentCreate(PaymentBase):
    """Fields required to create a payment."""

    customer_id: uuid.UUID


class PaymentRead(PaymentBase):
    """Payment response schema."""

    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
