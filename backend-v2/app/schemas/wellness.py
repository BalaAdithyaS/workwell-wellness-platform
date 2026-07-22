"""Wellness request / response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WellnessCreate(BaseModel):
    """Schema for form-submitted wellness data."""

    mood_score: int = Field(..., ge=1, le=10)
    stress_level: int = Field(..., ge=1, le=10)
    burnout_risk: int = Field(..., ge=1, le=10)
    sentiment: str = Field(..., min_length=1, max_length=50)
    recommendation: str = Field(..., min_length=1)
    notes: str | None = None
    sleep_hours: float | None = None
    energy_level: str | None = None


class WellnessResponse(BaseModel):
    """Serialized wellness entry returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    source: str
    mood_score: int
    stress_level: int
    burnout_risk: int
    sentiment: str
    recommendation: str
    notes: str | None
    sleep_hours: float | None = None
    energy_level: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
