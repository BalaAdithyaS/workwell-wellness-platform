"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.database.base import Base
from app.database.db import engine, SessionLocal

import app.models.user  # noqa: F401
import app.models.team  # noqa: F401
import app.models.wellness  # noqa: F401
import app.models.voice  # noqa: F401

from app.api import auth, wellness, voice, analytics, manager, teams
from app.middleware.logging import RequestLoggingMiddleware

settings = get_settings()

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready.")
    yield
    engine.dispose()
    logger.info("Database connections disposed.")


# ── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="WorkWell API",
    description="AI-powered Employee Wellness Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware (order matters: last added = first executed) ────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — returns JSON, not HTML."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(wellness.router)
app.include_router(voice.router)
app.include_router(analytics.router)
app.include_router(manager.router)


# ── Health Endpoint ───────────────────────────────────────────
@app.get("/", tags=["health"])
def health_check() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok", "service": "workwell-api"}


@app.get("/health", tags=["health"])
def detailed_health() -> dict[str, str]:
    """Health check that verifies database connectivity."""
    result: dict[str, str] = {
        "status": "ok",
        "service": "workwell-api",
        "database": "ok",
    }
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Health check DB failure: %s", exc)
        result["database"] = "unavailable"
        result["status"] = "degraded"
    return result
