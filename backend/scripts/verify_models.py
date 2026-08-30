"""Quick verification that models can be queried via SQLAlchemy."""

import asyncio
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models import Customer, Payment, RecoveryCase, RecoveryAction, AuditLog


async def verify():
    async with async_session_factory() as session:
        # Count all records
        customers = await session.scalar(select(func.count()).select_from(Customer))
        payments = await session.scalar(select(func.count()).select_from(Payment))
        cases = await session.scalar(select(func.count()).select_from(RecoveryCase))
        actions = await session.scalar(select(func.count()).select_from(RecoveryAction))
        logs = await session.scalar(select(func.count()).select_from(AuditLog))

        print(f"Customers:        {customers}")
        print(f"Payments:         {payments}")
        print(f"Recovery Cases:   {cases}")
        print(f"Recovery Actions: {actions}")
        print(f"Audit Logs:       {logs}")

        # Test relationship loading
        stmt = select(RecoveryCase).where(RecoveryCase.status == "recovered")
        result = await session.execute(stmt)
        recovered = result.scalar_one_or_none()
        if recovered:
            await session.refresh(recovered, ["payment", "customer", "audit_logs"])
            print(f"\nRecovered case:")
            print(f"  Customer:  {recovered.customer.name}")
            print(f"  Payment:   {recovered.payment.razorpay_payment_id}")
            print(f"  At Risk:   INR {recovered.amount_at_risk / 100:,.2f}")
            print(f"  Recovered: INR {recovered.recovered_amount / 100:,.2f}")
            print(f"  Audit Log entries: {len(recovered.audit_logs)}")

        # Revenue metrics
        total_at_risk = await session.scalar(
            select(func.sum(RecoveryCase.amount_at_risk))
        )
        total_recovered = await session.scalar(
            select(func.sum(RecoveryCase.recovered_amount))
        )
        print(f"\nRevenue Metrics:")
        print(f"  Total at Risk:  INR {(total_at_risk or 0) / 100:,.2f}")
        print(f"  Total Recovered: INR {(total_recovered or 0) / 100:,.2f}")

        print("\n[OK] All model queries passed!")


if __name__ == "__main__":
    asyncio.run(verify())
