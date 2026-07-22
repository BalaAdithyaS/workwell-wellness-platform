"""Voice wellness business logic — orchestrates transcript -> Gemini -> DB."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.voice import VoiceConversation
from app.models.wellness import Source, WellnessEntry
from app.schemas.voice import (
    VoiceAnalysisResult,
    VoiceChatMessage,
    VoiceChatResponse,
    VoiceResponse,
)
from app.services.gemini_service import analyze_transcript, generate_next_question

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


async def process_voice(
    db: Session, user_id: uuid.UUID, transcript: str
) -> VoiceResponse:
    """Full pipeline: Gemini analysis → save conversation + wellness entry.

    Everything is committed together. If the wellness insert fails after the
    conversation was added, the entire transaction is rolled back.
    """
    result: VoiceAnalysisResult = await analyze_transcript(transcript)

    conversation = VoiceConversation(
        user_id=user_id,
        conversation=transcript,
        summary=result.summary,
    )
    db.add(conversation)
    db.flush()

    entry = WellnessEntry(
        user_id=user_id,
        source=Source.VOICE,
        mood_score=result.mood_score,
        stress_level=result.stress_level,
        burnout_risk=result.burnout_risk,
        sentiment=result.sentiment,
        recommendation=result.recommendation,
        notes=None,
        sleep_hours=result.sleep_hours,
        energy_level=result.energy_level,
    )
    db.add(entry)
    db.flush()

    db.commit()
    db.refresh(conversation)
    db.refresh(entry)

    logger.info(
        "Voice pipeline complete: conversation=%s entry=%s user=%s",
        conversation.id,
        entry.id,
        user_id,
    )

    return VoiceResponse(
        wellness_entry_id=entry.id,
        voice_conversation_id=conversation.id,
        mood_score=result.mood_score,
        stress_level=result.stress_level,
        burnout_risk=result.burnout_risk,
        sentiment=result.sentiment,
        recommendation=result.recommendation,
        summary=result.summary,
    )


async def process_chat(
    conversation: list[VoiceChatMessage],
) -> VoiceChatResponse:
    """Generate the next coaching question based on conversation history."""
    messages = [{"role": m.role, "content": m.content} for m in conversation]
    return await generate_next_question(messages)


def get_voice_history(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[VoiceConversation]:
    """Return voice conversations for a user, newest first."""
    limit = min(limit, MAX_PAGE_SIZE)
    return (
        db.execute(
            select(VoiceConversation)
            .where(VoiceConversation.user_id == user_id)
            .order_by(VoiceConversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
