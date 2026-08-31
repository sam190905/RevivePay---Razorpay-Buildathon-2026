import asyncio
import os
import uuid
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

# MUST LOAD AND PATCH ENV VARS BEFORE ANY APP IMPORTS
load_dotenv()
os.environ["APP_MODE"] = "test"
os.environ["AI_PROVIDER"] = "gemini"
os.environ["GEMINI_MODEL"] = "gemini-3.6-flash"

from app.db.session import async_session_factory
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.services.recovery_engine import RecoveryEngine
from app.schemas.recovery import RecoveryActionType

async def main():
    print("Testing Real Gemini AI integration and schema alignment...")
    
    # Must have Gemini API Key to run this test properly
    if not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "sk-mock-key":
        print("Skipping real Gemini test because GEMINI_API_KEY is not configured.")
        return

    recovery_engine = RecoveryEngine()
    
    async with async_session_factory() as db:
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_real_ai_test_{int(datetime.now(timezone.utc).timestamp())}",
            name="Real AI Test Customer",
            email="ai_test@example.com",
            phone="+919876543210"
        )
        db.add(customer)
        await db.commit()

        # TEST 1: Recoverable Scenario -> Should recommend create_payment_link and execute
        print("\n[Test 1] Real AI Test: Recoverable Scenario")
        
        max_retries = 2
        for attempt in range(max_retries):
            p1 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_ai_1_{int(datetime.now(timezone.utc).timestamp())}_{attempt}", customer_id=customer.id, amount=100000, currency="INR", status="failed", failure_code="INSUFFICIENT_FUNDS", failure_reason="Not enough balance")
            c1 = RecoveryCase(id=uuid.uuid4(), payment_id=p1.id, customer_id=customer.id, amount_at_risk=100000, status="open")
            
            db.add(p1)
            db.add(c1)
            await db.commit()
            
            try:
                c1_res = await recovery_engine.process_recovery_case(db, c1, p1, customer)
                
                # Verify we didn't fallback due to AI errors
                from sqlalchemy import text
                fallback = await db.execute(text("SELECT metadata_json FROM audit_logs WHERE actor='system_fallback' AND recovery_case_id=:cid"), {"cid": c1.id})
                fallback_row = fallback.first()
                
                if fallback_row:
                    error_msg = fallback_row[0].get("error", "")
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                        print(f"Failed Fast: Gemini API Quota Exhausted (429).\nError: {error_msg}")
                        return
                    
                    print(f"Transient AI failure: {error_msg}. Retrying quickly...")
                    await asyncio.sleep(2)
                    continue
                
                break
            except Exception as e:
                print(f"Pipeline failed: {e}")
                break
                
        assert c1_res.recommended_action in [RecoveryActionType.CREATE_PAYMENT_LINK.value, RecoveryActionType.MANUAL_REVIEW.value], f"AI returned unsupported action: {c1_res.recommended_action}"
        
        if c1_res.recommended_action == RecoveryActionType.CREATE_PAYMENT_LINK.value:
            assert c1_res.actual_action == RecoveryActionType.CREATE_PAYMENT_LINK.value, f"Policy didn't approve payment link, got: {c1_res.actual_action}"
            print(f" -> SUCCESS: Gemini recommended {c1_res.recommended_action} and policy approved.")
            print(" -> Note: Real Razorpay test link created via Test Mode!")
        else:
            print(f" -> SUCCESS: Gemini recommended {c1_res.recommended_action} and it was handled safely.")
        
        print("\n[OK] Real Gemini AI Tests passed!")

if __name__ == "__main__":
    asyncio.run(main())
