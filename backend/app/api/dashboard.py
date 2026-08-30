from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.recovery_case import RecoveryCase
from app.models.payment import Payment

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get high-level summary metrics for the dashboard."""
    # Calculate revenue at risk (total amount_at_risk for all cases)
    at_risk_query = await db.execute(select(func.sum(RecoveryCase.amount_at_risk)))
    revenue_at_risk = at_risk_query.scalar() or 0

    # Calculate recoverable revenue (cases not in failed status or open cases with score > 0.5)
    recoverable_query = await db.execute(
        select(func.sum(RecoveryCase.amount_at_risk))
        .where(RecoveryCase.status.in_(["open", "manual_review", "recovered"]))
    )
    recoverable_revenue = recoverable_query.scalar() or 0

    # Calculate revenue recovered
    recovered_query = await db.execute(select(func.sum(RecoveryCase.recovered_amount)))
    revenue_recovered = recovered_query.scalar() or 0

    # Calculate recovery attempted
    attempted_query = await db.execute(
        select(func.sum(RecoveryCase.amount_at_risk))
        .where(RecoveryCase.actual_action.isnot(None))
    )
    recovery_attempted = attempted_query.scalar() or 0

    # Count total cases
    cases_count_query = await db.execute(select(func.count(RecoveryCase.id)))
    cases_processed = cases_count_query.scalar() or 0

    # Calculate recovery rate
    recovery_rate = (revenue_recovered / recovery_attempted * 100) if recovery_attempted > 0 else 0

    # Funnel metrics
    funnel = [
        {"name": "Total Failed Payments", "value": cases_processed},
        {"name": "Cases Created", "value": cases_processed},
        {"name": "Actions Recommended", "value": await _get_count(db, RecoveryCase.recommended_action.isnot(None))},
        {"name": "Actions Executed", "value": await _get_count(db, RecoveryCase.actual_action.isnot(None))},
        {"name": "Successfully Recovered", "value": await _get_count(db, RecoveryCase.status == "recovered")}
    ]

    # Action distribution
    actions_query = await db.execute(
        select(RecoveryCase.actual_action, func.count(RecoveryCase.id))
        .where(RecoveryCase.actual_action.isnot(None))
        .group_by(RecoveryCase.actual_action)
    )
    actions_distribution = [{"action": row[0], "count": row[1]} for row in actions_query.all()]

    return {
        "metrics": {
            "revenueAtRisk": revenue_at_risk,
            "recoverableRevenue": recoverable_revenue,
            "recoveryAttempted": recovery_attempted,
            "revenueRecovered": revenue_recovered,
            "recoveryRate": round(recovery_rate, 2),
            "casesProcessed": cases_processed,
        },
        "funnel": funnel,
        "actions": actions_distribution
    }

async def _get_count(db: AsyncSession, condition) -> int:
    query = await db.execute(select(func.count(RecoveryCase.id)).where(condition))
    return query.scalar() or 0
