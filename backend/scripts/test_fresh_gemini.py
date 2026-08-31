import asyncio
import os
import uuid
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# 1. Load .env FIRST
load_dotenv()
os.environ["APP_MODE"] = "test"

# 2. Now import app modules
from app.config import settings
from app.schemas.recovery import RecoveryActionType, AIDiagnosisResult
from app.services.ai_agent import AIRecoveryAgent
from app.services.recovery_engine import RecoveryEngine
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.recovery_case import RecoveryCase
from app.db.session import async_session_factory
from pydantic import ValidationError

async def main():
    print("=== ENVIRONMENT VERIFICATION ===")
    print(f"APP_MODE={settings.app_mode}")
    print(f"AI_PROVIDER={settings.ai_provider}")
    print(f"GEMINI_MODEL={settings.gemini_model}")
    print("API_KEY loaded:", bool(settings.gemini_api_key) and settings.gemini_api_key != "sk-mock-key")
    
    print("\n=== RUNTIME SCHEMA VERIFICATION ===")
    actions = [a.value for a in RecoveryActionType]
    print(f"RecoveryActionType members: {actions}")
    schema = AIDiagnosisResult.model_json_schema()
    print("AIDiagnosisResult schema allows:", schema["$defs"]["RecoveryActionType"]["enum"])
    
    print("\n=== PROMPT VERIFICATION ===")
    agent = AIRecoveryAgent()
    p_dummy = Payment(amount=1000, currency="INR", failure_code="TEST", failure_reason="Test")
    c_dummy = Customer(email="test@example.com")
    prompt = agent._build_prompt(p_dummy, c_dummy)
    print("Effective allowed-action prompt constraint:")
    # Extract just the constraints line
    for line in prompt.split('\n'):
        if "Your allowed recovery actions are:" in line or "You may only select from" in line or "create_payment_link" in line:
            print(f" -> {line}")
            
    print("\n=== VALIDATION REJECTION TEST ===")
    invalid_json = json.dumps({
        "classification": "temporary_failure",
        "confidence": 0.9,
        "recommended_action": "retry_payment",
        "reason": "Test"
    })
    try:
        AIDiagnosisResult.model_validate_json(invalid_json)
        print("FAILED: Pydantic accepted retry_payment!")
        assert False
    except ValidationError as e:
        print("SUCCESS: Pydantic rejected retry_payment correctly.")
        print(f"Error snippet: {str(e).splitlines()[1].strip()}")
        
    if not settings.gemini_api_key or settings.gemini_api_key == "sk-mock-key":
        print("Skipping real Gemini test due to missing key.")
        return

    print("\n=== REAL GEMINI PIPELINE TEST ===")
    engine = RecoveryEngine()
    
    async with async_session_factory() as db:
        customer = Customer(
            id=uuid.uuid4(),
            external_customer_id=f"cust_fresh_test_{int(datetime.now(timezone.utc).timestamp())}",
            name="Fresh Test",
            email="fresh@example.com",
            phone="+919876543210"
        )
        db.add(customer)
        
        import time
        max_retries = 5
        for attempt in range(max_retries):
            p = Payment(
                id=uuid.uuid4(), 
                razorpay_payment_id=f"pay_fresh_{int(datetime.now(timezone.utc).timestamp())}_{attempt}", 
                customer_id=customer.id, 
                amount=50000, 
                currency="INR", 
                status="failed", 
                failure_code="INSUFFICIENT_FUNDS", 
                failure_reason="Insufficient balance"
            )
            c = RecoveryCase(
                id=uuid.uuid4(), 
                payment_id=p.id, 
                customer_id=customer.id, 
                amount_at_risk=50000, 
                status="open"
            )
            db.add(p)
            db.add(c)
            await db.commit()
            
            try:
                res = await engine.process_recovery_case(db, c, p, customer)
                # check audit logs to ensure it wasn't fallback
                from sqlalchemy import text
                fallback = await db.execute(text("SELECT id FROM audit_logs WHERE actor='system_fallback' AND recovery_case_id=:cid"), {"cid": c.id})
                if fallback.first():
                    print("HIT FALLBACK, RETRYING IN 20 SECONDS TO CLEAR RATE LIMIT...")
                    await asyncio.sleep(20)
                    continue
                break
            except Exception as e:
                print("Failed to process:", e)
                break
        
        print(f"AI Recommended Action: {res.recommended_action}")
        print(f"Policy Approved Action: {res.actual_action}")
        print(f"Case Status: {res.status}")
        
        assert res.recommended_action == "create_payment_link"
        assert res.actual_action == "create_payment_link"
        print("SUCCESS: Pipeline executed successfully from end to end.")

if __name__ == "__main__":
    asyncio.run(main())
