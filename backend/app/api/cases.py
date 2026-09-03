from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, cast, String, func
from sqlalchemy.orm import joinedload
import uuid

from app.db.session import get_db
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment
from app.models.customer import Customer
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/search")
async def search_recovery_cases(
    q: str = Query("", min_length=0, description="Search query"),
    db: AsyncSession = Depends(get_db),
):
    """Search recovery cases across customer name, email, payment ID, status, amount, and failure reason."""
    q = q.strip()
    if not q:
        return []

    pattern = f"%{q}%"

    # Build OR conditions for text-based ILIKE search
    conditions = [
        Customer.name.ilike(pattern),
        Customer.email.ilike(pattern),
        Payment.razorpay_payment_id.ilike(pattern),
        RecoveryCase.status.ilike(pattern),
        Payment.failure_reason.ilike(pattern),
        Payment.failure_code.ilike(pattern),
        RecoveryCase.recommended_action.ilike(pattern),
        RecoveryCase.actual_action.ilike(pattern),
    ]

    # If query looks like a UUID, also try exact case ID match
    try:
        query_uuid = uuid.UUID(q)
        conditions.append(RecoveryCase.id == query_uuid)
    except ValueError:
        pass

    # If query is numeric, try matching amount in paise (user might type "1000" for ₹1000)
    try:
        amount_val = int(float(q) * 100)  # Convert rupees to paise
        conditions.append(Payment.amount == amount_val)
        # Also try raw paise match
        conditions.append(Payment.amount == int(q))
    except (ValueError, OverflowError):
        pass

    query = await db.execute(
        select(RecoveryCase, Customer, Payment)
        .join(Customer, RecoveryCase.customer_id == Customer.id)
        .join(Payment, RecoveryCase.payment_id == Payment.id)
        .where(or_(*conditions))
        .order_by(RecoveryCase.opened_at.desc())
        .limit(10)
    )

    results = []
    for case, customer, payment in query.all():
        results.append({
            "id": str(case.id),
            "customer_name": customer.name,
            "customer_email": customer.email,
            "amount": payment.amount,
            "currency": payment.currency,
            "failure_reason": payment.failure_reason or payment.failure_code,
            "recovery_probability": case.recovery_probability,
            "recommended_action": case.recommended_action,
            "actual_action": case.actual_action,
            "status": case.status,
            "opened_at": case.opened_at,
            "recovered_amount": case.recovered_amount,
        })
    return results


@router.get("")
async def get_recovery_cases(db: AsyncSession = Depends(get_db)):
    """Get all recovery cases."""
    query = await db.execute(
        select(RecoveryCase, Customer, Payment)
        .join(Customer, RecoveryCase.customer_id == Customer.id)
        .join(Payment, RecoveryCase.payment_id == Payment.id)
        .order_by(RecoveryCase.opened_at.desc())
    )
    
    results = []
    for case, customer, payment in query.all():
        results.append({
            "id": str(case.id),
            "customer_name": customer.name,
            "customer_email": customer.email,
            "amount": payment.amount,
            "currency": payment.currency,
            "failure_reason": payment.failure_reason or payment.failure_code,
            "recovery_probability": case.recovery_probability,
            "recommended_action": case.recommended_action,
            "actual_action": case.actual_action,
            "status": case.status,
            "opened_at": case.opened_at,
            "recovered_amount": case.recovered_amount
        })
    return results

@router.get("/{case_id}")
async def get_recovery_case_detail(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get details for a specific recovery case."""
    query = await db.execute(
        select(RecoveryCase, Customer, Payment)
        .join(Customer, RecoveryCase.customer_id == Customer.id)
        .join(Payment, RecoveryCase.payment_id == Payment.id)
        .where(RecoveryCase.id == case_id)
    )
    row = query.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case, customer, payment = row
    
    # Get audit logs
    audit_query = await db.execute(
        select(AuditLog)
        .where(AuditLog.recovery_case_id == case_id)
        .order_by(AuditLog.timestamp.asc())
    )
    logs = audit_query.scalars().all()
    
    return {
        "case": {
            "id": str(case.id),
            "amount_at_risk": case.amount_at_risk,
            "reason": case.reason,
            "recovery_probability": case.recovery_probability,
            "status": case.status,
            "recommended_action": case.recommended_action,
            "actual_action": case.actual_action,
            "recovered_amount": case.recovered_amount,
            "opened_at": case.opened_at,
            "closed_at": case.closed_at
        },
        "customer": {
            "id": str(customer.id),
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone
        },
        "payment": {
            "id": str(payment.id),
            "razorpay_payment_id": payment.razorpay_payment_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "failure_code": payment.failure_code,
            "failure_reason": payment.failure_reason
        },
        "audit_logs": [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "actor": log.actor,
                "action": log.action,
                "status": log.status,
                "metadata_json": log.metadata_json,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
    }

@router.post("/{case_id}/sync")
async def sync_recovery_case_status(case_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Sync a recovery case status directly from Razorpay (for local testing without webhooks)."""
    from app.models.recovery_action import RecoveryAction
    from app.integrations.razorpay_client import razorpay_client
    from app.services.recovery_engine import recovery_engine
    
    case = await db.scalar(select(RecoveryCase).where(RecoveryCase.id == case_id))
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    action = await db.scalar(
        select(RecoveryAction)
        .where(RecoveryAction.recovery_case_id == case.id)
        .order_by(RecoveryAction.executed_at.desc())
        .limit(1)
    )
    
    if not action or not action.result:
        return {"status": "ok", "message": "No actionable result to sync"}
        
    import json
    try:
        res_dict = json.loads(action.result)
        provider_id = res_dict.get("provider_id")
    except:
        provider_id = None
        
    if not provider_id or provider_id.startswith("plink_sim_"):
        return {"status": "ok", "message": "Not a real payment link"}
        
    try:
        link_data = await razorpay_client.fetch_payment_link(provider_id)
        status = link_data.get("status")
        amount_paid = link_data.get("amount_paid", 0)
        
        if status == "paid" or amount_paid > 0:
            await recovery_engine.verify_recovery_result(db, case, amount_paid)
            return {"status": "success", "message": "Status synced and updated to recovered"}
            
        return {"status": "ok", "message": f"Payment link status is {status}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from Razorpay: {e}")

