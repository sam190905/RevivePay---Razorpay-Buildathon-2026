"""Pydantic schemas for dashboard summary."""

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    """Aggregated revenue recovery metrics for the overview dashboard."""

    revenue_at_risk: int = 0
    recoverable_revenue: int = 0
    recovery_attempted: int = 0
    revenue_recovered: int = 0
    recovery_rate: float = 0.0
    total_cases: int = 0
    open_cases: int = 0
    closed_cases: int = 0
