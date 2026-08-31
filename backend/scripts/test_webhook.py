"""Test script to verify Razorpay webhook handling.

This script manually sends test requests to the local FastAPI server
to verify signature validation and idempotency.

Run with: python -m scripts.test_webhook
Note: Make sure the FastAPI server is running on port 8000.
"""

import hmac
import hashlib
import json
import asyncio
import httpx
from datetime import datetime, timezone

# Load secret from settings
from app.config import settings

def get_secret():
    return settings.razorpay_webhook_secret

async def main():
    print("Testing Razorpay Webhook Endpoint...")
    url = "http://localhost:8000/webhooks/razorpay"
    
    # 1. Create a dummy payload
    payload = {
        "entity": "event",
        "account_id": "acc_12345",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_sim_123456",
                    "amount": 1000,
                    "currency": "INR",
                    "status": "failed"
                }
            }
        },
        "created_at": int(datetime.now(timezone.utc).timestamp())
    }
    
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    
    # 2. Generate valid signature
    signature = hmac.new(
        get_secret().encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    event_id = f"evnt_test_{int(datetime.now(timezone.utc).timestamp())}"
    
    headers = {
        "x-razorpay-signature": signature,
        "x-razorpay-event-id": event_id,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # Test 1: Valid webhook
        print("\n[Test 1] Sending valid webhook...")
        resp = await client.post(url, content=payload_bytes, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200, "Valid webhook failed"
        
        # Test 2: Idempotency (Duplicate event)
        print("\n[Test 2] Sending duplicate webhook (same event ID)...")
        resp = await client.post(url, content=payload_bytes, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 200
        assert resp.json().get("message") == "Duplicate event ignored", "Idempotency check failed"
        
        # Test 3: Invalid signature
        print("\n[Test 3] Sending webhook with invalid signature...")
        invalid_headers = headers.copy()
        invalid_headers["x-razorpay-signature"] = "invalid_sig_12345"
        invalid_headers["x-razorpay-event-id"] = f"evnt_test_{int(datetime.now(timezone.utc).timestamp()) + 1}"
        
        resp = await client.post(url, content=payload_bytes, headers=invalid_headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 400
        assert resp.json().get("detail") == "Invalid signature", "Invalid signature check failed"

        # Test 4: Missing headers
        print("\n[Test 4] Sending webhook with missing headers...")
        resp = await client.post(url, content=payload_bytes, headers={"Content-Type": "application/json"})
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        assert resp.status_code == 400

        # Test 5: Duplicate payment_link.paid (different event IDs)
        print("\n[Test 5] Sending payment_link.paid...")
        paid_payload = {
            "entity": "event",
            "account_id": "acc_12345",
            "event": "payment_link.paid",
            "contains": ["payment_link"],
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_test_123456",
                        "amount": 1000,
                        "amount_paid": 1000,
                        "reference_id": "pay_sim_123456",
                        "status": "paid"
                    }
                }
            },
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }
        paid_payload_bytes = json.dumps(paid_payload, separators=(',', ':')).encode('utf-8')
        paid_sig_1 = hmac.new(get_secret().encode('utf-8'), paid_payload_bytes, hashlib.sha256).hexdigest()
        
        # First payment_link.paid event
        paid_event_id_1 = f"evnt_paid_1_{int(datetime.now(timezone.utc).timestamp())}"
        headers_paid_1 = {
            "x-razorpay-signature": paid_sig_1,
            "x-razorpay-event-id": paid_event_id_1,
            "Content-Type": "application/json"
        }
        # We might need to wait for the recovery case to be fully processed from Test 1
        await asyncio.sleep(2)
        resp = await client.post(url, content=paid_payload_bytes, headers=headers_paid_1)
        print(f"Status (First paid): {resp.status_code}")
        assert resp.status_code == 200

        # Second payment_link.paid event (different event_id to bypass webhook idempotency, test application idempotency)
        print("\n[Test 5 continued] Sending duplicate payment_link.paid (different event ID)...")
        paid_event_id_2 = f"evnt_paid_2_{int(datetime.now(timezone.utc).timestamp()) + 1}"
        headers_paid_2 = {
            "x-razorpay-signature": paid_sig_1,
            "x-razorpay-event-id": paid_event_id_2,
            "Content-Type": "application/json"
        }
        resp = await client.post(url, content=paid_payload_bytes, headers=headers_paid_2)
        print(f"Status (Second paid): {resp.status_code}")
        assert resp.status_code == 200
        print("Note: Check server logs to ensure 'Ignoring duplicate verification' was printed and revenue was not double-counted.")

    print("\n[OK] All webhook tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
