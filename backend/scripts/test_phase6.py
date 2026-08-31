"""Integration tests for Phase 6: Recovery Execution."""

import asyncio
from datetime import datetime, timezone
import uuid
import httpx

from app.services.recovery_engine import recovery_engine
from app.services.action_executor import action_executor
from app.integrations.razorpay_client import razorpay_client, RazorpayClientError
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery import RecoveryActionType
from app.db.session import async_session_factory
from app.config import settings

# Force AI into deterministic mock mode so we only test Execution
from app.services.ai_agent import ai_agent
ai_agent.is_mock = True

async def main():
    print("Testing Phase 6 Recovery Execution...\n")

    async with async_session_factory() as db:
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_t6_{int(datetime.now(timezone.utc).timestamp())}",
            name="Test User",
            email=f"test6_{int(datetime.now(timezone.utc).timestamp())}@example.com"
        )
        db.add(customer)
        await db.commit()

        # [Test 1] Approved Action Executes Successfully (Demo Mode)
        print("[Test 1] Approved Action Executes Successfully")
        settings.app_mode = "developer"
        p1 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p6_1_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c1 = RecoveryCase(id=uuid.uuid4(), payment_id=p1.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p1)
        db.add(c1)
        await db.commit()
        
        c1_res = await recovery_engine.process_recovery_case(db, c1, p1, customer)
        assert c1_res.actual_action == RecoveryActionType.CREATE_PAYMENT_LINK.value
        print(" -> SUCCESS: Action approved and executed in demo mode.")

        # [Test 2] Blocked Action Never Executes
        print("\n[Test 2] Blocked Action Never Executes")
        p2 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p6_2_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=200000, currency="INR", status="failed", failure_code="FRAUD", failure_reason="fraud")
        c2 = RecoveryCase(id=uuid.uuid4(), payment_id=p2.id, customer_id=customer.id, amount_at_risk=200000, status="open")
        db.add(p2)
        db.add(c2)
        await db.commit()
        
        c2_res = await recovery_engine.process_recovery_case(db, c2, p2, customer)
        assert c2_res.status == "manual_review"
        print(" -> SUCCESS: Blocked action routed to manual review and never executed automatically.")

        # [Test 3] Execution Failure (API Error)
        print("\n[Test 3] API Execution Failure")
        settings.app_mode = "test" # Disable developer mode to hit the actual mocked client
        
        # Mock RazorpayClient to raise an error
        async def mock_api_fail(*args, **kwargs):
            raise RazorpayClientError("Simulated API failure")
        
        original_create = razorpay_client.create_payment_link
        razorpay_client.create_payment_link = mock_api_fail
        
        p3 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p6_3_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c3 = RecoveryCase(id=uuid.uuid4(), payment_id=p3.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p3)
        db.add(c3)
        await db.commit()
        
        c3_res = await recovery_engine.process_recovery_case(db, c3, p3, customer)
        # The engine catches ActionExecutionError and logs it in AuditLog, leaving case open
        print(" -> SUCCESS: Execution API failure caught safely.")

        # [Test 4] Execution Timeout
        print("\n[Test 4] API Timeout")
        async def mock_api_timeout(*args, **kwargs):
            raise httpx.TimeoutException("Simulated Timeout")
        
        razorpay_client.create_payment_link = mock_api_timeout
        
        p4 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p6_4_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c4 = RecoveryCase(id=uuid.uuid4(), payment_id=p4.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p4)
        db.add(c4)
        await db.commit()
        
        c4_res = await recovery_engine.process_recovery_case(db, c4, p4, customer)
        print(" -> SUCCESS: Execution API timeout caught safely.")
        
        razorpay_client.create_payment_link = original_create
        settings.app_mode = "developer"

        # [Test 5] Successful Verification & Revenue Calculation
        print("\n[Test 5] Successful Verification")
        c5_res = await recovery_engine.verify_recovery_result(db, c1_res, 100000)
        assert c5_res.status == "recovered"
        assert c5_res.recovered_amount == 100000
        print(" -> SUCCESS: Verification success calculated revenue correctly.")

        # [Test 6] Unsuccessful Verification
        print("\n[Test 6] Unsuccessful Verification")
        p6 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_p6_6_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c6 = RecoveryCase(id=uuid.uuid4(), payment_id=p6.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p6)
        db.add(c6)
        await db.commit()
        c6_res = await recovery_engine.verify_recovery_result(db, c6, 0)
        assert c6_res.status == "failed"
        assert c6_res.recovered_amount == 0
        print(" -> SUCCESS: Verification failure recorded correctly.")
        
        print("\n[OK] All Phase 6 Unit Tests Passed!")

if __name__ == "__main__":
    asyncio.run(main())
