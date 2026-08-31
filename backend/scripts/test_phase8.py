import asyncio
import os
import json
import uuid
import httpx
from sqlalchemy.future import select
from datetime import datetime, timezone

from app.db.session import async_session_factory
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.audit_log import AuditLog
from app.config import settings
from app.api.demo import _send_webhook

async def main():
    print("Testing Phase 8: Developer Mode Lifecycle and Idempotency...")
    
    test_payment_id = f"pay_test_{int(datetime.now(timezone.utc).timestamp())}"
    test_email = f"test_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    event_id = f"evnt_test_{int(datetime.now(timezone.utc).timestamp())}"
    
    failed_payload = {
        "entity": "event",
        "account_id": "acc_12345",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": test_payment_id,
                    "entity": "payment",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "failed",
                    "method": "card",
                    "error_code": "INSUFFICIENT_FUNDS",
                    "error_description": "Payment failed due to insufficient funds",
                    "email": test_email,
                    "contact": "+919876583461"
                }
            }
        },
        "created_at": int(datetime.now(timezone.utc).timestamp())
    }
    
    # 1. Trigger Payment Failed Webhook
    print(f"\n[Test 1] Triggering payment failed webhook...")
    await _send_webhook(failed_payload)
    await asyncio.sleep(2) # Allow background tasks to complete
    
    async with async_session_factory() as db:
        case = await db.scalar(select(RecoveryCase).where(RecoveryCase.payment_id.in_(
            select(Payment.id).where(Payment.razorpay_payment_id == test_payment_id)
        )))
        
        assert case is not None, "Recovery case not created"
        case_id = str(case.id)
        print(f" -> Case Created: {case_id}")
        
        # Verify it stays in processing, and recovered_amount = 0
        assert case.status == "processing", f"Expected 'processing', got {case.status}"
        assert case.recovered_amount == 0, f"Expected 0 recovered, got {case.recovered_amount}"
        print(f" -> Case remains non-terminal and unrecovered. (status: {case.status})")

    # 2. Simulate Payment Link creation and verify it didn't recover revenue
    print(f"\n[Test 2] Simulating payment link generation (developer mode)...")
    async with httpx.AsyncClient() as client:
        # Simulate payment explicitly using the new endpoint
        res = await client.post(
            f"{settings.backend_url}/demo/scenarios/simulate-payment", 
            json={"case_id": case_id}
        )
        assert res.status_code == 200, f"Simulation failed: {res.text}"
        
        await asyncio.sleep(2) # Allow verification logic to run

    # 3. Verify it's now recovered
    print(f"\n[Test 3] Verifying payment attribution...")
    async with async_session_factory() as db:
        case = await db.scalar(select(RecoveryCase).where(RecoveryCase.id == case_id))
        
        assert case.status == "recovered", f"Expected 'recovered', got {case.status}"
        assert case.recovered_amount == 250000, f"Expected 250000, got {case.recovered_amount}"
        print(f" -> Case status is {case.status} and amount recovered is {case.recovered_amount}")
        
    # 4. Idempotency test
    print(f"\n[Test 4] Submitting duplicate simulated payment...")
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{settings.backend_url}/demo/scenarios/simulate-payment", 
            json={"case_id": case_id}
        )
        assert res.status_code == 200
        await asyncio.sleep(2)

    async with async_session_factory() as db:
        case = await db.scalar(select(RecoveryCase).where(RecoveryCase.id == case_id))
        # ensure it's still just 250000
        assert case.recovered_amount == 250000, "Idempotency failed: Amount increased"
        print(" -> Duplicate safely ignored. Revenue is unchanged.")

    print("\n[OK] Phase 8 Developer Mode tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
