"""API endpoints for handling webhooks."""

import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import WebhookEvent
from app.integrations.razorpay_utils import verify_webhook_signature, SignatureVerificationError

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle incoming Razorpay webhooks.
    
    Verifies signature and ensures idempotency.
    """
    signature = request.headers.get("x-razorpay-signature")
    event_id = request.headers.get("x-razorpay-event-id")
    
    if not signature:
        logger.warning("Razorpay webhook missing signature")
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature")

    if not event_id:
        logger.warning("Razorpay webhook missing event ID")
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Event-Id")

    # Read raw body for signature verification
    payload_body = await request.body()
    
    # 1. Verify Signature
    try:
        verify_webhook_signature(payload_body, signature)
    except SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Check Idempotency
    # We check if this event ID has already been processed
    existing_event = await db.scalar(
        select(WebhookEvent).where(WebhookEvent.razorpay_event_id == event_id)
    )
    
    if existing_event:
        logger.info(f"Duplicate webhook event ignored: {event_id}")
        return {"status": "ok", "message": "Duplicate event ignored"}

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")
    logger.info(f"Processing Razorpay webhook: {event_type} (ID: {event_id})")

    # 3. Store the webhook event for idempotency
    webhook_event = WebhookEvent(
        razorpay_event_id=event_id,
        event_type=event_type or "unknown",
        payload=payload
    )
    db.add(webhook_event)
    await db.commit()

    # 4. Handle specific events
    if event_type == "payment.failed":
        logger.info(f"Received payment.failed event: {event_id}")
        
        # We need to import the other models locally or at module level
        # To avoid circular imports if any, but in webhooks it should be fine.
        from app.models.customer import Customer
        from app.models.payment import Payment
        from app.models.recovery_case import RecoveryCase
        from app.models.audit_log import AuditLog
        import uuid

        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        if not payment_data:
            logger.error("No payment data found in payload")
            return {"status": "ok", "message": "Ignored: No payment data"}

        razorpay_payment_id = payment_data.get("id")
        amount = payment_data.get("amount", 0)
        currency = payment_data.get("currency", "INR")
        status = payment_data.get("status", "failed")
        order_id = payment_data.get("order_id")
        method = payment_data.get("method")
        error_code = payment_data.get("error_code")
        error_description = payment_data.get("error_description")
        email = payment_data.get("email")
        contact = payment_data.get("contact")

        # Step 4a: Find or Create Customer
        customer = None
        if email or contact:
            # Try to find by email
            if email:
                customer = await db.scalar(select(Customer).where(Customer.email == email))
            # Try by contact if not found
            if not customer and contact:
                customer = await db.scalar(select(Customer).where(Customer.phone == contact))
            
        if not customer:
            # Create a new dummy customer record
            customer = Customer(
                external_customer_id=f"ext_{uuid.uuid4().hex[:8]}",
                name=payment_data.get("notes", {}).get("name", "Unknown Customer"),
                email=email,
                phone=contact,
            )
            db.add(customer)
            await db.flush() # get customer.id

        # Step 4b: Upsert Payment
        payment = await db.scalar(select(Payment).where(Payment.razorpay_payment_id == razorpay_payment_id))
        if payment:
            # Update existing
            payment.status = status
            payment.failure_code = error_code
            payment.failure_reason = error_description
        else:
            # Create new
            payment = Payment(
                razorpay_payment_id=razorpay_payment_id,
                customer_id=customer.id,
                order_id=order_id,
                amount=amount,
                currency=currency,
                status=status,
                method=method,
                failure_code=error_code,
                failure_reason=error_description
            )
            db.add(payment)
            
        await db.flush() # get payment.id

        # Step 4c: Create RecoveryCase if not exists
        recovery_case = await db.scalar(select(RecoveryCase).where(RecoveryCase.payment_id == payment.id))
        if not recovery_case and status == "failed":
            recovery_case = RecoveryCase(
                payment_id=payment.id,
                customer_id=customer.id,
                amount_at_risk=amount,
                reason=error_description or error_code or "Payment failed",
                status="open"
            )
            db.add(recovery_case)
            await db.flush() # get recovery_case.id
            
            # Step 4d: Create AuditLog
            audit_log = AuditLog(
                recovery_case_id=recovery_case.id,
                event_type="case_created",
                actor="system",
                action="Created recovery case from webhook",
                status="success",
                metadata_json={"razorpay_event_id": event_id, "error_code": error_code}
            )
            db.add(audit_log)
            
        await db.commit()
        
        # Phase 4: Trigger the Deterministic Recovery Engine
        from app.services.recovery_engine import recovery_engine
        
        try:
            await recovery_engine.process_recovery_case(db, recovery_case, payment, customer)
            logger.info(f"Successfully processed recovery workflow for {razorpay_payment_id}")
        except Exception as e:
            logger.error(f"Error processing recovery case: {e}")
            
    elif event_type == "payment_link.paid":
        logger.info(f"Received payment_link.paid event: {event_id}")
        link_data = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        reference_id = link_data.get("reference_id")
        amount_paid = link_data.get("amount_paid", 0)

        if not reference_id:
            logger.error("No reference_id found in payment_link.paid payload")
            return {"status": "ok", "message": "Ignored: No reference_id"}

        from app.models.recovery_case import RecoveryCase
        
        # In our implementation, reference_id is the payment.id
        recovery_case = await db.scalar(select(RecoveryCase).where(RecoveryCase.payment_id == reference_id))
        
        if recovery_case:
            from app.services.recovery_engine import recovery_engine
            try:
                await recovery_engine.verify_recovery_result(db, recovery_case, amount_paid)
                logger.info(f"Successfully verified recovery for case {recovery_case.id}")
            except Exception as e:
                logger.error(f"Error verifying recovery case: {e}")
        else:
            logger.warning(f"No recovery case found for reference_id: {reference_id}")
            
    else:
        logger.info(f"Unhandled event type: {event_type}")

    return {"status": "ok"}
