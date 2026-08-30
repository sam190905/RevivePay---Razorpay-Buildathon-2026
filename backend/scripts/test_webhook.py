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

    print("\n[OK] All webhook tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
