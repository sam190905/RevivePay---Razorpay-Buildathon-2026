"""Pydantic schemas for recovery engine data structures."""

from enum import Enum
from pydantic import BaseModel, Field

class RecoveryActionType(str, Enum):
    """Fixed allowlist of recovery actions."""
    RETRY_PAYMENT = "retry_payment"
    CREATE_PAYMENT_LINK = "create_payment_link"
    SEND_RECOVERY_REMINDER = "send_recovery_reminder"
    MANUAL_REVIEW = "manual_review"

class PolicyOutcome(str, Enum):
    """Possible outcomes from the policy engine."""
    APPROVE = "APPROVE"
    BLOCK = "BLOCK"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class ClassificationResult(BaseModel):
    """Result of failure classification."""
    failure_category: str = Field(description="e.g. temporary_failure, insufficient_funds, fraud")
    description: str | None = None

class PolicyDecision(BaseModel):
    """The deterministic policy decision."""
    outcome: PolicyOutcome
    action: RecoveryActionType
    risk_level: str = Field(default="low")
    reason: str
    violated_rule: str | None = None

class AIDiagnosisResult(BaseModel):
    """Structured output expected from the LLM."""
    classification: str = Field(description="e.g. temporary_failure, insufficient_funds, fraud")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    recommended_action: RecoveryActionType = Field(description="Action recommended by the AI from the allowlist")
    reason: str = Field(description="Concise explanation for the diagnosis")

