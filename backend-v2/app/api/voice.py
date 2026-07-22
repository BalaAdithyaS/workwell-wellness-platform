"""Voice wellness endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.schemas.voice import (
    VoiceAnalyzeRequest,
    VoiceChatRequest,
    VoiceChatResponse,
    VoiceConversationResponse,
    VoiceResponse,
)
from app.services import voice_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])

MAX_TRANSCRIPT_LENGTH = 50000

_GEMINI_QUOTA_KEYWORDS = ("429", "quota", "RESOURCE_EXHAUSTED")


def _is_quota_error(msg: str) -> bool:
    """Return True if the error message indicates Gemini quota exhaustion."""
    lower = msg.lower()
    return any(kw in msg or kw.lower() in lower for kw in _GEMINI_QUOTA_KEYWORDS)


def _is_timeout_error(msg: str) -> bool:
    """Return True if the error message indicates a timeout."""
    return "timeout" in msg.lower()


@router.post(
    "/analyze", response_model=VoiceResponse, status_code=status.HTTP_201_CREATED
)
async def analyze_voice(
    payload: VoiceAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VoiceResponse:
    """Analyze a voice transcript via Gemini and persist results."""
    if len(payload.conversation) > MAX_TRANSCRIPT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Transcript too long. Maximum {MAX_TRANSCRIPT_LENGTH} characters.",
        )
    try:
        return await voice_service.process_voice(
            db, current_user.id, payload.conversation
        )
    except Exception as exc:
        logger.exception("Voice analysis failed for user=%s", current_user.id)
        error_msg = str(exc)
        if _is_quota_error(error_msg):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI analysis is temporarily unavailable because the Gemini API quota has been reached. Please try again later.",
            )
        if _is_timeout_error(error_msg):
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="AI analysis timed out. Please try again with a shorter conversation.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Voice analysis failed: {error_msg}",
        )


@router.post("/chat", response_model=VoiceChatResponse)
async def chat_voice(
    payload: VoiceChatRequest,
    current_user: User = Depends(get_current_user),
) -> VoiceChatResponse:
    """Generate the next conversational wellness question."""
    try:
        return await voice_service.process_chat(payload.conversation)
    except Exception as exc:
        logger.exception("Voice chat failed for user=%s", current_user.id)
        error_msg = str(exc)
        if _is_quota_error(error_msg):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI coaching is temporarily unavailable because the Gemini API quota has been reached. Please try again later.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not generate next question: {error_msg}",
        )


@router.get("/history", response_model=list[VoiceConversationResponse])
def voice_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[VoiceConversationResponse]:
    """Return voice conversations for the authenticated user with pagination."""
    rows = voice_service.get_voice_history(db, current_user.id, skip=skip, limit=limit)
    return [VoiceConversationResponse.model_validate(r) for r in rows]
