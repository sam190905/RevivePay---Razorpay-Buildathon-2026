import asyncio
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy.future import select

from app.db.session import async_session_factory
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.recovery_case import RecoveryCase
from app.services.action_executor import ActionExecutor, ActionExecutionError
from app.schemas.recovery import RecoveryActionType

async def main():
    print("Testing ActionExecutor Safety boundary...")
    
    executor = ActionExecutor()
    
    # 1. Test supported action (create_payment_link) in dev mode
    print("\n[Test 1] Supported Action (create_payment_link)")
    p1 = Payment(id=uuid.uuid4(), razorpay_payment_id=f"pay_safety_{uuid.uuid4().hex[:8]}", customer_id=uuid.uuid4(), amount=100000, currency="INR", status="failed")
    c1 = Customer(id=p1.customer_id, external_customer_id="cust_mock", name="Test Cust", email="test@example.com")
    
    try:
        res = await executor.execute(RecoveryActionType.CREATE_PAYMENT_LINK, p1, c1)
        assert res["status"] == "success"
        print(" -> SUCCESS: Executed supported action correctly.")
    except Exception as e:
        print(f" -> FAILED: {str(e)}")
        assert False

    # 2. Test manual review (also supported without external call)
    print("\n[Test 2] Supported Action (manual_review)")
    try:
        res = await executor.execute(RecoveryActionType.MANUAL_REVIEW, p1, c1)
        assert res["status"] == "success"
        print(" -> SUCCESS: Executed manual_review safely.")
    except Exception as e:
        print(f" -> FAILED: {str(e)}")
        assert False

    # 3. Test unsupported action boundary
    print("\n[Test 3] Unsupported Action Boundary")
    try:
        # Cast an unsupported string into the type
        invalid_action = "retry_payment"
        await executor.execute(invalid_action, p1, c1) # type: ignore
        assert False, "Should have raised ActionExecutionError"
    except ActionExecutionError as e:
        assert "Unsupported action for auto-execution" in str(e)
        print(" -> SUCCESS: Safely blocked unsupported action from execution.")
        
    print("\n[OK] ActionExecutor safety verified!")

if __name__ == "__main__":
    asyncio.run(main())
