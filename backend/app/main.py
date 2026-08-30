"""RevivePay — FastAPI application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify database connection on startup, cleanup on shutdown."""
    # Startup: check DB connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("[OK] Database connection verified")
    except Exception as e:
        print(f"[WARN] Database connection failed: {e}")
        print("  The app will start but database operations will fail.")

    yield

    # Shutdown: dispose engine
    await engine.dispose()
    print("[OK] Database engine disposed")


from app.api import api_router

app = FastAPI(
    title="RevivePay",
    description="AI-powered revenue recovery system for Razorpay",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)

# CORS — allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "revivepay",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
