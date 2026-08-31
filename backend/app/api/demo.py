from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import uuid
import time
import asyncio
import httpx
from pydantic import BaseModel

from app.db.session import get_db
from app.config import settings

router = APIRouter()

class DemoScenarioRequest(BaseModel):
    scenario: str # "successful_recovery", "payment_link_recovery", "blocked_recovery", "failed_execution", "duplicate_webhook"

@router.post("/scenarios")
async def trigger_demo_scenario(request: DemoScenarioRequest, background_tasks: BackgroundTasks):
    """Trigger a demo scenario by hitting the webhook endpoint with a synthetic payload."""
    
    failure_code = "GATEWAY_ERROR"
    failure_reason = "timeout"
    amount = 100000 # 1000 INR
    
    if request.scenario == "blocked_recovery":
        failure_code = "FRAUD"
        failure_reason = "Suspected fraud"
        amount = 500000
    elif request.scenario == "failed_execution":
        failure_code = "GATEWAY_ERROR"
        amount = 499999 # Special amount to trigger failure in ActionExecutor
    elif request.scenario == "payment_link_recovery":
        failure_code = "INSUFFICIENT_FUNDS"
        failure_reason = "Insufficient funds in customer account"
        amount = 250000
    
    payment_id = f"pay_demo_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    failed_payload = {
        "entity": "event",
        "account_id": "acc_1234567890",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "entity": "payment",
                    "amount": amount,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "error_code": failure_code,
                    "error_description": failure_reason,
                    "email": f"demo_{uuid.uuid4().hex[:4]}@example.com",
                    "contact": "9876543210"
                }
            }
        },
        "created_at": int(time.time())
    }
    
    paid_payload = {
        "entity": "event",
        "account_id": "acc_1234567890",
        "event": "payment_link.paid",
        "contains": ["payment_link"],
        "payload": {
            "payment_link": {
                "entity": {
                    "id": f"plink_demo_{uuid.uuid4().hex[:8]}",
                    "entity": "payment_link",
                    "amount": amount,
                    "amount_paid": amount,
                    "reference_id": payment_id,
                    "status": "paid"
                }
            }
        },
        "created_at": int(time.time()) + 3
    }
    
    background_tasks.add_task(_run_scenario, request.scenario, failed_payload, paid_payload)
    
    return {"status": "success", "message": f"Triggered scenario: {request.scenario}", "payment_id": payment_id}

async def _run_scenario(scenario: str, failed_payload: Dict[str, Any], paid_payload: Dict[str, Any]):
    """Execute the sequence of webhooks for the scenario."""
    await _send_webhook(failed_payload)
    
    if scenario == "duplicate_webhook":
        await asyncio.sleep(0.5)
        await _send_webhook(failed_payload)
        
    if scenario in ["successful_recovery", "payment_link_recovery"]:
        # Give the backend time to process the failure and generate the link
        await asyncio.sleep(4)
        await _send_webhook(paid_payload)

async def _send_webhook(payload: Dict[str, Any]):
    """Send the payload to the webhook endpoint."""
    import hmac
    import hashlib
    import json
    
    body = json.dumps(payload, separators=(',', ':'))
    secret = settings.razorpay_webhook_secret
    signature = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{settings.backend_url}/webhooks/razorpay",
                json=payload,
                headers={
                    "X-Razorpay-Signature": signature,
                    "X-Razorpay-Event-Id": f"evnt_demo_{uuid.uuid4().hex[:8]}"
                }
            )
        except Exception as e:
            print(f"Failed to send demo webhook: {e}")
