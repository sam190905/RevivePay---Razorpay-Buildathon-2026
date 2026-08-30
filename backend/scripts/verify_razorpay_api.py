"""Verify Razorpay live/test credentials and API connection."""

import asyncio
from app.config import settings
from app.integrations.razorpay_client import razorpay_client

async def main():
    print("Verifying Razorpay credentials loaded...")
    
    # Check if loaded from .env without printing values
    key_id = settings.razorpay_key_id
    key_secret = settings.razorpay_key_secret
    webhook_secret = settings.razorpay_webhook_secret
    
    if not key_id or key_id == "test_key_id":
        print("[FAIL] RAZORPAY_KEY_ID not loaded properly.")
        return
        
    if not key_secret or key_secret == "test_key_secret":
        print("[FAIL] RAZORPAY_KEY_SECRET not loaded properly.")
        return
        
    if not webhook_secret or webhook_secret == "test_webhook_secret_123":
        print("[FAIL] RAZORPAY_WEBHOOK_SECRET not loaded properly.")
        return
        
    print("[OK] Secrets loaded correctly.")
    print("Testing connection to Razorpay API (read-only)...")
    
    try:
        response = await razorpay_client.fetch_all_payments(count=1)
        if "items" in response:
            print("[OK] Successfully connected to Razorpay Test API.")
            print(f"     Fetched {len(response['items'])} payments.")
        else:
            print("[FAIL] Unexpected response format from Razorpay.")
    except Exception as e:
        print(f"[FAIL] Error communicating with Razorpay: {e}")

if __name__ == "__main__":
    asyncio.run(main())
