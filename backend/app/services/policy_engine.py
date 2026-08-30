"""Deterministic policy engine for recovery actions."""

import logging
from app.schemas.recovery import PolicyDecision, PolicyOutcome, RecoveryActionType

logger = logging.getLogger(__name__)

class PolicyEngine:
    """Evaluates rules to decide if a recovery action is allowed."""

    def __init__(self, risk_threshold: float = 0.2, max_amount_auto: int = 500000):
        # max_amount_auto in paise (e.g., 500000 = 5000 INR)
        self.risk_threshold = risk_threshold
        self.max_amount_auto = max_amount_auto

    def evaluate(self, amount: int, recovery_score: float, failure_category: str, proposed_action: RecoveryActionType) -> PolicyDecision:
        """
        Evaluate if the proposed action is permitted based on deterministic rules.
        """
        logger.info(f"Evaluating policy: amount={amount}, score={recovery_score}, category={failure_category}, action={proposed_action}")

        # Rule 1: Fraud is always blocked
        if failure_category == "fraud":
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                action=RecoveryActionType.MANUAL_REVIEW,
                risk_level="high",
                reason="Fraudulent transactions cannot be auto-recovered.",
                violated_rule="no_fraud_recovery"
            )

        # Rule 2: Too risky / Low probability of recovery
        if recovery_score < self.risk_threshold:
            return PolicyDecision(
                outcome=PolicyOutcome.BLOCK,
                action=RecoveryActionType.MANUAL_REVIEW,
                risk_level="high",
                reason=f"Recovery score ({recovery_score}) below threshold ({self.risk_threshold}).",
                violated_rule="minimum_recovery_score"
            )

        # Rule 3: High value transactions need manual review
        if amount > self.max_amount_auto:
            return PolicyDecision(
                outcome=PolicyOutcome.MANUAL_REVIEW,
                action=RecoveryActionType.MANUAL_REVIEW,
                risk_level="medium",
                reason=f"Amount ({amount}) exceeds automatic recovery limit ({self.max_amount_auto}).",
                violated_rule="max_amount_exceeded"
            )

        # Rule 4: Action restrictions (e.g. invalid action)
        if proposed_action not in [RecoveryActionType.CREATE_PAYMENT_LINK, RecoveryActionType.RETRY_PAYMENT]:
             return PolicyDecision(
                outcome=PolicyOutcome.MANUAL_REVIEW,
                action=RecoveryActionType.MANUAL_REVIEW,
                risk_level="low",
                reason=f"Action {proposed_action} requires manual processing.",
                violated_rule="unsupported_auto_action"
            )

        # Allowed
        return PolicyDecision(
            outcome=PolicyOutcome.APPROVE,
            action=proposed_action,
            risk_level="low",
            reason="Payment is eligible and rules passed.",
            violated_rule=None
        )

policy_engine = PolicyEngine()
