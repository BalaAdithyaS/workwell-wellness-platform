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
    
    try:
        with SessionLocal() as db:
            db.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS company VARCHAR(200) DEFAULT 'WorkWell' NOT NULL"))
            db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS company VARCHAR(200) DEFAULT 'WorkWell' NOT NULL"))
            
            # Create ENUM type safely
            db.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'source_enum') THEN CREATE TYPE source_enum AS ENUM ('FORM', 'VOICE'); END IF; END $$;"))
            
            # Add all columns for wellness_entries
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS source source_enum DEFAULT 'FORM' NOT NULL"))
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS sleep_hours FLOAT"))
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS energy_level VARCHAR(50)"))
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS burnout_risk INTEGER DEFAULT 0 NOT NULL"))
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS sentiment VARCHAR(50) DEFAULT 'Neutral' NOT NULL"))
            db.execute(text("ALTER TABLE wellness_entries ADD COLUMN IF NOT EXISTS recommendation TEXT DEFAULT '' NOT NULL"))
            
            db.commit()
            logger.info("Successfully ensured missing columns exist in all tables.")
    except Exception as exc:
        logger.error("Schema migration failed: %s", exc)
        
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

import httpx
@app.get("/gemini-test", tags=["health"])
def test_gemini_api_key():
    import json
    key = settings.GEMINI_API_KEY
    is_loaded = bool(key)
    key_length = len(key) if key else 0
    key_prefix = key[:5] if key else ""
    key_suffix = key[-5:] if key else ""
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
    try:
        resp = httpx.post(url, json=payload, headers={"Content-Type": "application/json", "x-goog-api-key": key}, timeout=10.0)
        return {
            "key_loaded": is_loaded,
            "key_length": key_length,
            "key_prefix": key_prefix,
            "key_suffix": key_suffix,
            "gemini_status": resp.status_code,
            "gemini_response": resp.json() if resp.text else ""
        }
    except Exception as e:
        return {"error": str(e)}
