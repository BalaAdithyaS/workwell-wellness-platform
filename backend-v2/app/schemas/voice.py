"""Voice request / response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class VoiceAnalyzeRequest(BaseModel):
    """Transcript sent from the frontend after voice session."""

    conversation: str = Field(..., min_length=1)


class VoiceAnalysisResult(BaseModel):
    """Structured AI output extracted from the voice transcript."""

    mood_score: int = Field(..., ge=1, le=10)
    stress_level: int = Field(..., ge=1, le=10)
    burnout_risk: int = Field(..., ge=1, le=10)
    sleep_hours: float | None = None
    energy_level: str | None = None
    sentiment: str
    recommendation: str
    summary: str


class VoiceResponse(BaseModel):
    """Returned after voice analysis — includes wellness data and conversation id."""

    wellness_entry_id: uuid.UUID
    voice_conversation_id: uuid.UUID
    mood_score: int
    stress_level: int
    burnout_risk: int
    sentiment: str
    recommendation: str
    summary: str


class VoiceChatMessage(BaseModel):
    """A single message in the coaching conversation."""

    role: str = Field(..., pattern=r"^(coach|user)$")
    content: str = Field(..., min_length=1)


class VoiceChatRequest(BaseModel):
    """Conversation history sent to generate the next question."""

    conversation: list[VoiceChatMessage] = Field(..., min_length=1)


class VoiceChatResponse(BaseModel):
    """Next question from the coach, or signal that the session is complete."""

    next_question: str | None = None
    done: bool = False


class VoiceConversationResponse(BaseModel):
    """A single voice conversation record for history."""

    id: uuid.UUID
    user_id: uuid.UUID
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}
