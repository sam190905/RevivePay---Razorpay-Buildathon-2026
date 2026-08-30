"""Integration test for Phase 3: Recovery Case Pipeline.

Tests that a payment.failed webhook successfully creates/updates:
- Customer
- Payment
- RecoveryCase
- AuditLog
"""

import asyncio
import json
import hmac
import hashlib
from datetime import datetime, timezone
import httpx
from sqlalchemy import select

# Configure environment for tests
from app.config import settings
from app.db.session import async_session_factory
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.models.audit_log import AuditLog
from app.models.webhook_event import WebhookEvent

def get_secret():
    return settings.razorpay_webhook_secret

async def main():
    print("Testing Phase 3 Pipeline...")
    
    url = "http://localhost:8000/webhooks/razorpay"
    
    test_payment_id = f"pay_test_{int(datetime.now(timezone.utc).timestamp())}"
    test_email = f"test_{int(datetime.now(timezone.utc).timestamp())}@example.com"
    event_id = f"evnt_test_{int(datetime.now(timezone.utc).timestamp())}"
    
    payload = {
        "entity": "event",
        "account_id": "acc_12345",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": test_payment_id,
                    "entity": "payment",
                    "amount": 250000, # 2500 INR
                    "currency": "INR",
                    "status": "failed",
                    "order_id": "order_test_123",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to insufficient funds",
                    "email": test_email,
                    "contact": f"+9198765{str(int(datetime.now(timezone.utc).timestamp()))[-5:]}"
                }
            }
        },
        "created_at": int(datetime.now(timezone.utc).timestamp())
    }
    
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(get_secret().encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
    headers = {
        "x-razorpay-signature": signature,
        "x-razorpay-event-id": event_id,
        "Content-Type": "application/json"
    }

    print(f"\n[Test 1] Sending first webhook for {test_payment_id}...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=payload_bytes, headers=headers)
        assert resp.status_code == 200, f"Webhook failed: {resp.text}"
        print("[OK] Webhook processed.")
        
    print("\n[Test 2] Verifying database state...")
    async with async_session_factory() as db:
        # Check Customer
        customer = await db.scalar(select(Customer).where(Customer.email == test_email))
        assert customer is not None, "Customer was not created"
        print(f"[OK] Customer created: {customer.id}")
        
        # Check Payment
        payment = await db.scalar(select(Payment).where(Payment.razorpay_payment_id == test_payment_id))
        assert payment is not None, "Payment was not created"
        assert payment.customer_id == customer.id
        assert payment.amount == 250000
        assert payment.status == "failed"
        assert payment.failure_code == "BAD_REQUEST_ERROR"
        print(f"[OK] Payment created: {payment.id}")
        
        # Check Recovery Case
        case = await db.scalar(select(RecoveryCase).where(RecoveryCase.payment_id == payment.id))
        assert case is not None, "RecoveryCase was not created"
        assert case.amount_at_risk == 250000
        assert case.status == "open"
        print(f"[OK] RecoveryCase created: {case.id}")
        
        # Check Audit Log
        audit = await db.scalar(select(AuditLog).where(AuditLog.recovery_case_id == case.id))
        assert audit is not None, "AuditLog was not created"
        assert audit.event_type == "case_created"
        print(f"[OK] AuditLog created: {audit.id}")
        
    print("\n[Test 3] Sending duplicate webhook to verify idempotency pipeline...")
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, content=payload_bytes, headers=headers)
        assert resp.status_code == 200
        assert resp.json().get("message") == "Duplicate event ignored"
        
    async with async_session_factory() as db:
        cases = (await db.execute(select(RecoveryCase).where(RecoveryCase.payment_id == payment.id))).scalars().all()
        assert len(cases) == 1, f"Expected 1 recovery case, got {len(cases)}"
        print("[OK] Duplicate webhook safely ignored.")
        
    print("\n[OK] All Phase 3 tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
