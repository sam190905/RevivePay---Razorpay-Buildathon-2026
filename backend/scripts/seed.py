"""Seed script — populates the database with sample data for development/demo.

Usage:
    python -m scripts.seed

All data is clearly labeled as synthetic/simulated.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.db.session import async_session_factory, engine
from app.models import Customer, Payment, RecoveryCase, RecoveryAction, AuditLog

# ---------------------------------------------------------------------------
# Sample customers
# ---------------------------------------------------------------------------
CUSTOMERS = [
    {
        "external_customer_id": "cust_sim_001",
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "phone": "+919876543210",
    },
    {
        "external_customer_id": "cust_sim_002",
        "name": "Rahul Mehta",
        "email": "rahul.mehta@example.com",
        "phone": "+919876543211",
    },
    {
        "external_customer_id": "cust_sim_003",
        "name": "Anjali Verma",
        "email": "anjali.verma@example.com",
        "phone": "+919876543212",
    },
    {
        "external_customer_id": "cust_sim_004",
        "name": "Vikram Singh",
        "email": "vikram.singh@example.com",
        "phone": "+919876543213",
    },
    {
        "external_customer_id": "cust_sim_005",
        "name": "Neha Patel",
        "email": "neha.patel@example.com",
        "phone": "+919876543214",
    },
]

# ---------------------------------------------------------------------------
# Sample failed payments (amounts in paise)
# ---------------------------------------------------------------------------
now = datetime.now(timezone.utc)

PAYMENTS = [
    {
        "razorpay_payment_id": "pay_sim_temp_001",
        "customer_idx": 0,
        "order_id": "order_sim_001",
        "amount": 249900,  # ₹2,499.00
        "currency": "INR",
        "status": "failed",
        "method": "upi",
        "failure_reason": "Payment processing failed due to bank server timeout",
        "failure_code": "GATEWAY_ERROR",
    },
    {
        "razorpay_payment_id": "pay_sim_insuf_002",
        "customer_idx": 1,
        "order_id": "order_sim_002",
        "amount": 799900,  # ₹7,999.00
        "currency": "INR",
        "status": "failed",
        "method": "card",
        "failure_reason": "Insufficient funds in the account",
        "failure_code": "BAD_REQUEST_ERROR",
    },
    {
        "razorpay_payment_id": "pay_sim_temp_003",
        "customer_idx": 2,
        "order_id": "order_sim_003",
        "amount": 149900,  # ₹1,499.00
        "currency": "INR",
        "status": "failed",
        "method": "netbanking",
        "failure_reason": "Transaction timed out at bank end",
        "failure_code": "GATEWAY_ERROR",
    },
    {
        "razorpay_payment_id": "pay_sim_high_004",
        "customer_idx": 3,
        "order_id": "order_sim_004",
        "amount": 4999900,  # ₹49,999.00
        "currency": "INR",
        "status": "failed",
        "method": "card",
        "failure_reason": "Card declined by issuing bank",
        "failure_code": "BAD_REQUEST_ERROR",
    },
    {
        "razorpay_payment_id": "pay_sim_temp_005",
        "customer_idx": 4,
        "order_id": "order_sim_005",
        "amount": 59900,  # ₹599.00
        "currency": "INR",
        "status": "failed",
        "method": "wallet",
        "failure_reason": "Wallet service temporarily unavailable",
        "failure_code": "GATEWAY_ERROR",
    },
    {
        "razorpay_payment_id": "pay_sim_recovered_006",
        "customer_idx": 0,
        "order_id": "order_sim_006",
        "amount": 349900,  # ₹3,499.00
        "currency": "INR",
        "status": "failed",
        "method": "upi",
        "failure_reason": "UPI transaction timeout",
        "failure_code": "GATEWAY_ERROR",
    },
]

# ---------------------------------------------------------------------------
# Sample recovery cases
# ---------------------------------------------------------------------------
RECOVERY_CASES = [
    {
        "payment_idx": 0,
        "recovery_probability": 0.87,
        "status": "open",
        "reason": "temporary_failure",
        "recommended_action": "retry_payment",
    },
    {
        "payment_idx": 1,
        "recovery_probability": 0.45,
        "status": "open",
        "reason": "insufficient_funds",
        "recommended_action": "create_payment_link",
    },
    {
        "payment_idx": 2,
        "recovery_probability": 0.82,
        "status": "open",
        "reason": "temporary_failure",
        "recommended_action": "retry_payment",
    },
    {
        "payment_idx": 3,
        "recovery_probability": 0.23,
        "status": "open",
        "reason": "card_declined",
        "recommended_action": "manual_review",
    },
    {
        "payment_idx": 4,
        "recovery_probability": 0.91,
        "status": "open",
        "reason": "temporary_failure",
        "recommended_action": "retry_payment",
    },
    {
        # A completed case to show recovered revenue
        "payment_idx": 5,
        "recovery_probability": 0.84,
        "status": "recovered",
        "reason": "temporary_failure",
        "recommended_action": "retry_payment",
        "actual_action": "retry_payment",
        "recovered_amount": 349900,
    },
]


async def seed() -> None:
    """Insert sample data into the database."""

    async with async_session_factory() as session:
        # Check if data already exists
        count = await session.scalar(select(func.count()).select_from(Customer))
        if count and count > 0:
            print(f"[SKIP] Database already has {count} customers. Run with --force or truncate tables first.")
            return

        print("[SEED] Creating sample customers...")
        customers = []
        for c in CUSTOMERS:
            customer = Customer(**c)
            session.add(customer)
            customers.append(customer)
        await session.flush()

        print("[SEED] Creating sample failed payments...")
        payments = []
        for p in PAYMENTS:
            payment_data = {k: v for k, v in p.items() if k != "customer_idx"}
            payment_data["customer_id"] = customers[p["customer_idx"]].id
            payment_data["created_at"] = now - timedelta(hours=len(PAYMENTS) - len(payments))
            payment = Payment(**payment_data)
            session.add(payment)
            payments.append(payment)
        await session.flush()

        print("[SEED] Creating sample recovery cases...")
        cases = []
        for rc in RECOVERY_CASES:
            payment = payments[rc["payment_idx"]]
            case_data = {
                "payment_id": payment.id,
                "customer_id": payment.customer_id,
                "amount_at_risk": payment.amount,
                "reason": rc["reason"],
                "recovery_probability": rc["recovery_probability"],
                "status": rc["status"],
                "recommended_action": rc["recommended_action"],
                "actual_action": rc.get("actual_action"),
                "recovered_amount": rc.get("recovered_amount", 0),
                "opened_at": payment.created_at + timedelta(seconds=5),
            }
            if rc["status"] == "recovered":
                case_data["closed_at"] = payment.created_at + timedelta(minutes=10)
            case = RecoveryCase(**case_data)
            session.add(case)
            cases.append(case)
        await session.flush()

        print("[SEED] Creating sample audit logs...")
        for i, case in enumerate(cases):
            # Case created event
            session.add(AuditLog(
                recovery_case_id=case.id,
                event_type="case_created",
                actor="system",
                action="Recovery case created from failed payment webhook",
                status="completed",
                metadata_json={
                    "payment_id": str(case.payment_id),
                    "amount_at_risk": case.amount_at_risk,
                    "simulated": True,
                },
                timestamp=case.opened_at,
            ))

            # For the recovered case, add additional audit entries
            if case.status == "recovered":
                session.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="ai_diagnosis",
                    actor="ai_agent",
                    action="AI diagnosed failure as temporary_failure with 0.84 confidence",
                    status="completed",
                    metadata_json={
                        "classification": "temporary_failure",
                        "confidence": 0.84,
                        "recommended_action": "retry_payment",
                        "simulated": True,
                    },
                    timestamp=case.opened_at + timedelta(seconds=2),
                ))
                session.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="policy_check",
                    actor="policy_engine",
                    action="Policy approved retry_payment action",
                    status="approved",
                    metadata_json={
                        "action": "retry_payment",
                        "risk_level": "low",
                        "simulated": True,
                    },
                    timestamp=case.opened_at + timedelta(seconds=3),
                ))
                session.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="action_executed",
                    actor="system",
                    action="Payment retry executed successfully",
                    status="success",
                    metadata_json={
                        "action_type": "retry_payment",
                        "recovered_amount": case.recovered_amount,
                        "simulated": True,
                    },
                    timestamp=case.opened_at + timedelta(minutes=5),
                ))
                session.add(AuditLog(
                    recovery_case_id=case.id,
                    event_type="case_closed",
                    actor="system",
                    action=f"Recovery case closed — INR {case.recovered_amount / 100:,.2f} recovered",
                    status="completed",
                    metadata_json={
                        "recovered_amount": case.recovered_amount,
                        "simulated": True,
                    },
                    timestamp=case.closed_at,
                ))

        await session.commit()

        print(f"[SEED] Done! Created:")
        print(f"  - {len(customers)} customers")
        print(f"  - {len(payments)} payments")
        print(f"  - {len(cases)} recovery cases")
        print(f"  - Audit log entries for all cases")
        print(f"  - All data is labeled as simulated")


if __name__ == "__main__":
    asyncio.run(seed())
