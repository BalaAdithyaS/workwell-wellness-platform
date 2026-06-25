from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.wellness import router as wellness_router
from app.api.analytics import router as analytics_router
from app.api.ai import router as ai_router
from app.api.conversation import router as conversation_router
from app.api.voice_assistant import router as voice_router

from app.database.db import Base, engine
from app.models.voice_assessment import VoiceAssessment

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WorkWell API",
    version="1.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://workwell-wellness-platform.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home Route
@app.get("/")
def home():
    return {
        "message": "WorkWell Backend Running"
    }

# API Routes
app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

app.include_router(
    wellness_router,
    prefix="/wellness",
    tags=["Wellness"]
)

app.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["Analytics"]
)

app.include_router(
    ai_router,
    prefix="/ai",
    tags=["AI"]
)

app.include_router(
    conversation_router,
    prefix="/conversation",
    tags=["Conversation"]
)

app.include_router(
    voice_router,
    prefix="/voice",
    tags=["Voice Assistant"]
)