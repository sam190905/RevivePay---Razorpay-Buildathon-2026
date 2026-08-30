"""API router configuration."""

from fastapi import APIRouter
from app.api.webhooks import router as webhooks_router

from app.api.dashboard import router as dashboard_router
from app.api.cases import router as cases_router
from app.api.demo import router as demo_router

api_router = APIRouter()
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(cases_router, prefix="/recovery-cases", tags=["cases"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])
