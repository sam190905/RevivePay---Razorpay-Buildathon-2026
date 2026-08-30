"""Unit tests for Phase 4: Deterministic Recovery Engine."""

import asyncio
from datetime import datetime, timezone
import uuid

from app.services.recovery_engine import recovery_engine
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.schemas.recovery import RecoveryActionType

# Mock the Razorpay action executor to avoid real API calls in tests
from app.services.action_executor import action_executor

async def mock_create_payment_link(payment: Payment, customer: Customer) -> dict:
    return {
        "status": "success",
        "result": "https://rzp.io/i/mocktestlink",
        "provider_id": "plink_mock123"
    }

action_executor._create_payment_link = mock_create_payment_link

# Use the real db session
from app.db.session import async_session_factory

async def main():
    print("Testing Phase 4 Deterministic Engine...\n")

    async with async_session_factory() as db:
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_test_{int(datetime.now(timezone.utc).timestamp())}",
            name="Test User",
            email=f"test_{int(datetime.now(timezone.utc).timestamp())}@example.com"
        )
        db.add(customer)
        await db.commit()

        # Test 1: Eligible Recovery (Gateway Error, low amount)
        print("[Test 1] Eligible Recovery (GATEWAY_ERROR, 1000 INR)")
        p1 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_t1_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="GATEWAY_ERROR", failure_reason="timeout")
        c1 = RecoveryCase(id=uuid.uuid4(), payment_id=p1.id, customer_id=customer.id, amount_at_risk=100000, status="open")
        db.add(p1)
        db.add(c1)
        await db.commit()

        c1_res = await recovery_engine.process_recovery_case(db, c1, p1, customer)
        assert c1_res.recommended_action == RecoveryActionType.CREATE_PAYMENT_LINK.value
        assert c1_res.actual_action == RecoveryActionType.CREATE_PAYMENT_LINK.value
        print(" -> SUCCESS: Approved and Payment Link Created.")

        # Test 2: Blocked Recovery (Fraud)
        print("\n[Test 2] Blocked Recovery (FRAUD)")
        p2 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_t2_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=200000, currency="INR", status="failed", failure_code="FRAUD", failure_reason="Suspected fraud")
        c2 = RecoveryCase(id=uuid.uuid4(), payment_id=p2.id, customer_id=customer.id, amount_at_risk=200000, status="open")
        db.add(p2)
        db.add(c2)
        await db.commit()

        c2_res = await recovery_engine.process_recovery_case(db, c2, p2, customer)
        assert c2_res.status == "manual_review"
        assert c2_res.actual_action == RecoveryActionType.MANUAL_REVIEW.value
        print(" -> SUCCESS: Fraud detected, action blocked, routed to manual review.")

        # Test 3: Manual Review (Amount Exceeded)
        print("\n[Test 3] Manual Review (High Amount)")
        p3 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_t3_{int(datetime.now(timezone.utc).timestamp())}", customer_id=customer.id, amount=600000, currency="INR", status="failed", failure_code="BAD_REQUEST_ERROR", failure_reason="insufficient")
        c3 = RecoveryCase(id=uuid.uuid4(), payment_id=p3.id, customer_id=customer.id, amount_at_risk=600000, status="open")
        db.add(p3)
        db.add(c3)
        await db.commit()

        c3_res = await recovery_engine.process_recovery_case(db, c3, p3, customer)
        assert c3_res.status == "manual_review"
        assert c3_res.actual_action == RecoveryActionType.MANUAL_REVIEW.value
        print(" -> SUCCESS: Amount > 5000 INR, routed to manual review.")
        
        # Test 4: Revenue Verification
        print("\n[Test 4] Revenue Verification")
        c1_verified = await recovery_engine.verify_recovery_result(db, c1, 100000)
        assert c1_verified.status == "recovered"
        assert c1_verified.recovered_amount == 100000
        print(" -> SUCCESS: Full recovery verified and calculated.")
        
        print("\n[OK] All Phase 4 Unit Tests Passed!")

if __name__ == "__main__":
    asyncio.run(main())
