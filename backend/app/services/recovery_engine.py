"""Deterministic recovery orchestrator."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_action import RecoveryAction
from app.models.audit_log import AuditLog
from app.schemas.recovery import ClassificationResult, PolicyDecision, PolicyOutcome, RecoveryActionType
from app.services.policy_engine import policy_engine
from app.services.action_executor import action_executor, ActionExecutionError

logger = logging.getLogger(__name__)


class RecoveryEngine:
    """Orchestrates the deterministic recovery workflow."""

    def classify_failure(self, payment: Payment) -> ClassificationResult:
        """Baseline failure classification using Razorpay error codes."""
        code = payment.failure_code or ""
        reason = (payment.failure_reason or "").lower()

        if "fraud" in reason or code == "FRAUD":
            return ClassificationResult(failure_category="fraud", description="Suspected fraud.")
        if code in ["BAD_REQUEST_ERROR", "INSUFFICIENT_FUNDS"] or "insufficient" in reason:
            return ClassificationResult(failure_category="insufficient_funds", description="Insufficient funds in customer account.")
        if code == "GATEWAY_ERROR" or "timeout" in reason:
            return ClassificationResult(failure_category="temporary_downtime", description="Bank or gateway downtime.")
        
        return ClassificationResult(failure_category="unknown_error", description="Unknown or generic failure.")

    def calculate_recovery_score(self, payment: Payment, classification: ClassificationResult) -> float:
        """Simple deterministic probability heuristic (0.0 - 1.0)."""
        score = 0.5  # base score

        # Adjust based on category
        if classification.failure_category == "temporary_downtime":
            score += 0.4  # highly recoverable
        elif classification.failure_category == "insufficient_funds":
            score += 0.1  # sometimes recoverable (salary day, etc)
        elif classification.failure_category == "fraud":
            return 0.0    # never recoverable

        # Adjust based on amount (smaller amounts generally easier to recover)
        if payment.amount < 100000:  # < 1000 INR
            score += 0.1
        elif payment.amount > 500000: # > 5000 INR
            score -= 0.1

        return min(max(score, 0.0), 1.0)

    def determine_action(self, classification: ClassificationResult) -> RecoveryActionType:
        """Map classification to a proposed action."""
        if classification.failure_category == "fraud":
            return RecoveryActionType.MANUAL_REVIEW
        # In this deterministic engine, we default to sending a payment link
        return RecoveryActionType.CREATE_PAYMENT_LINK

    async def process_recovery_case(self, db: AsyncSession, case: RecoveryCase, payment: Payment, customer: Customer) -> RecoveryCase:
        """Run the full recovery pipeline on a case."""
        case.status = "processing"
        await db.commit()

        # 1. Classification & Scoring (AI First, fallback to deterministic)
        from app.services.ai_agent import ai_agent, AIAgentError
        
        try:
            ai_result = await ai_agent.diagnose_failure(payment, customer)
            
            classification = ClassificationResult(
                failure_category=ai_result.classification, 
                description=ai_result.reason
            )
            score = ai_result.confidence
            proposed_action = ai_result.recommended_action
            
            # Determine the actual source: real OpenAI or mock/deterministic
            ai_actor = "system_fallback" if ai_agent.is_mock else "ai_agent"
            ai_action = (
                "Deterministic classification (mock AI)"
                if ai_agent.is_mock
                else "AI classified failure and calculated score"
            )
            
            db.add(AuditLog(
                recovery_case_id=case.id,
                event_type="ai_diagnosis",
                actor=ai_actor,
                action=ai_action,
                status="success",
                metadata_json=ai_result.model_dump()
            ))
            
        except AIAgentError as e:
            logger.warning(f"AI diagnosis failed, falling back to deterministic logic: {e}")
            classification = self.classify_failure(payment)
            proposed_action = self.determine_action(classification)
            
            db.add(AuditLog(
                recovery_case_id=case.id,
                event_type="ai_diagnosis",
                actor="system_fallback",
                action="Deterministic classification (AI fallback)",
                status="success",
                metadata_json={
                    "classification": payment.failure_reason or payment.failure_code or "Unknown",
                    "confidence": None,
                    "recommended_action": proposed_action.value,
                    "reason": "Fallback to deterministic rules.",
                    "error": str(e)
                }
            ))

            score = None

        case.recovery_probability = score

        # 4. Policy Check
        decision = policy_engine.evaluate(
            amount=payment.amount,
            recovery_score=score,
            failure_category=classification.failure_category,
            proposed_action=proposed_action
        )
        
        case.recommended_action = proposed_action.value
        case.actual_action = decision.action.value
        
        db.add(AuditLog(
            recovery_case_id=case.id,
            event_type="policy_check",
            actor="policy_engine",
            action=f"Policy decision: {decision.outcome.value}",
            status="success",
            metadata_json=decision.model_dump()
        ))

        # 5. Execution
        if decision.outcome == PolicyOutcome.APPROVE:
            db_action = RecoveryAction(
                recovery_case_id=case.id,
                action_type=decision.action.value,
                status="pending",
                amount=payment.amount
            )
            db.add(db_action)
            await db.flush() # get action id
            
            try:
                exec_result = await action_executor.execute(decision.action, payment, customer)
                db_action.status = "success"
                import json
                db_action.result = json.dumps(exec_result)
                
                db.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="action_executed",
                    actor="action_executor",
                    action=f"Executed {decision.action.value}",
                    status="success",
                    metadata_json=exec_result
                ))
            except ActionExecutionError as e:
                db_action.status = "failed"
                db_action.error = str(e)
                case.status = "failed"
                db.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="action_executed",
                    actor="action_executor",
                    action=f"Failed to execute {decision.action.value}",
                    status="failed",
                    metadata_json={"error": str(e)}
                ))
                
        elif decision.outcome == PolicyOutcome.BLOCK or decision.outcome == PolicyOutcome.MANUAL_REVIEW:
            case.status = "manual_review"
            db.add(AuditLog(
                recovery_case_id=case.id,
                event_type="action_executed",
                actor="system",
                action="Routed to manual review",
                status="success",
                metadata_json={"reason": decision.reason}
            ))

        await db.commit()
        return case

    async def verify_recovery_result(self, db: AsyncSession, case: RecoveryCase, amount_paid: int) -> RecoveryCase:
        """Verify the recovery outcome and calculate recovered revenue."""
        logger.info(f"Verifying recovery result for case {case.id}")
        
        if case.status in ["recovered", "partially_recovered"]:
            logger.info(f"RecoveryCase {case.id} is already in {case.status} status. Ignoring duplicate verification.")
            return case

        case.recovered_amount = amount_paid
        if amount_paid >= case.amount_at_risk:
            case.status = "recovered"
        elif amount_paid > 0:
            case.status = "partially_recovered"
        else:
            case.status = "failed"
            
        # Update Audit Log
        db.add(AuditLog(
            recovery_case_id=case.id,
            event_type="verification",
            actor="system",
            action=f"Verified recovery of {amount_paid} paise.",
            status="success",
            metadata_json={"recovered_amount": amount_paid, "new_status": case.status}
        ))
        
        await db.commit()
        return case

recovery_engine = RecoveryEngine()
