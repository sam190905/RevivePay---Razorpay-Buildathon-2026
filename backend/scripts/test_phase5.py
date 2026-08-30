"""Unit tests for Phase 5: AI Recovery Agent."""

import asyncio
from datetime import datetime, timezone
import uuid

from app.services.recovery_engine import recovery_engine
from app.services.ai_agent import ai_agent, AIAgentError
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery import RecoveryActionType, AIDiagnosisResult

# Mock the Razorpay action executor
from app.services.action_executor import action_executor

async def mock_create_payment_link(payment: Payment, customer: Customer) -> dict:
    return {
        "status": "success",
        "result": "https://rzp.io/i/mocktestlink",
        "provider_id": "plink_mock123"
    }

action_executor._create_payment_link = mock_create_payment_link

from app.db.session import async_session_factory

async def main():
    print("Testing Phase 5 AI Recovery Agent...\n")

    async with async_session_factory() as db:
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_t5_{int(datetime.now(timezone.utc).timestamp())}",
            name="Test User",
            email=f"test5_{int(datetime.now(timezone.utc).timestamp())}@example.com"
        )
        db.add(customer)
        await db.commit()

        # Ensure AI is in mock mode for standard tests
        original_mock_state = ai_agent.is_mock
        ai_agent.is_mock = True

        # Test 1: Valid AI Output (Gateway Error -> Temporary Failure)
        print("[Test 1] Valid AI Output (Mocked)")
        p1 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p5_1_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c1 = RecoveryCase(id=uuid.uuid4(), payment_id=p1.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p1)
        db.add(c1)
        await db.commit()

        c1_res = await recovery_engine.process_recovery_case(db, c1, p1, customer)
        assert c1_res.recommended_action == RecoveryActionType.CREATE_PAYMENT_LINK.value
        assert c1_res.recovery_probability == 0.85
        print(" -> SUCCESS: AI successfully diagnosed and policy approved.")

        # Test 2: AI Model Failure -> Deterministic Fallback
        print("\n[Test 2] AI Model Failure Fallback")
        # Force the AI to fail
        async def mock_fail(*args, **kwargs):
            raise AIAgentError("Simulated LLM outage")
            
        original_diagnose = ai_agent.diagnose_failure
        ai_agent.diagnose_failure = mock_fail
        
        p2 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p5_2_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=200000, currency="INR", status="failed", failure_code="INSUFFICIENT_FUNDS", failure_reason="insufficient")
        c2 = RecoveryCase(id=uuid.uuid4(), payment_id=p2.id, customer_id=customer.id, amount_at_risk=200000, status="open")
        db.add(p2)
        db.add(c2)
        await db.commit()

        c2_res = await recovery_engine.process_recovery_case(db, c2, p2, customer)
        # It should fallback to deterministic, which for insufficient_funds gives score of 0.5 + 0.1 = 0.6
        assert c2_res.recovery_probability == 0.6
        assert c2_res.recommended_action == RecoveryActionType.CREATE_PAYMENT_LINK.value
        print(" -> SUCCESS: LLM failure gracefully fell back to deterministic engine.")
        
        # Restore diagnose
        ai_agent.diagnose_failure = original_diagnose

        # Test 3: AI recommends something, but Policy Blocks it
        print("\n[Test 3] Policy Rejects AI Recommendation")
        # Force AI to recommend recovery for FRAUD
        async def mock_bad_advice(*args, **kwargs):
            return AIDiagnosisResult(
                classification="fraud",
                confidence=0.99,
                recommended_action=RecoveryActionType.CREATE_PAYMENT_LINK, # AI tries to create a link for fraud!
                reason="I'm a rogue AI and I want to recover fraud."
            )
            
        ai_agent.diagnose_failure = mock_bad_advice
        
        p3 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p5_3_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=150000, currency="INR", status="failed", failure_code="FRAUD", failure_reason="Suspected fraud")
        c3 = RecoveryCase(id=uuid.uuid4(), payment_id=p3.id, customer_id=customer.id, amount_at_risk=150000, status="open")
        db.add(p3)
        db.add(c3)
        await db.commit()
        
        c3_res = await recovery_engine.process_recovery_case(db, c3, p3, customer)
        assert c3_res.recommended_action == RecoveryActionType.CREATE_PAYMENT_LINK.value # AI's recommendation
        assert c3_res.actual_action == RecoveryActionType.MANUAL_REVIEW.value # Policy's enforcement
        assert c3_res.status == "manual_review"
        print(" -> SUCCESS: Deterministic policy engine blocked the AI's unsafe recommendation.")
        
        # Restore mock state
        ai_agent.diagnose_failure = original_diagnose
        ai_agent.is_mock = original_mock_state
        
        print("\n[OK] All Phase 5 Unit Tests Passed!")

if __name__ == "__main__":
    asyncio.run(main())
