"""Analytics request / response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class WellnessSummary(BaseModel):
    """Aggregated wellness stats for a user."""

    total_entries: int
    avg_mood: float
    avg_stress: float
    avg_burnout: float
    latest_sentiment: str | None
    form_entries: int
    voice_entries: int


class ChartDataPoint(BaseModel):
    """One point on the wellness-over-time chart."""

    date: datetime
    mood_score: int
    stress_level: int
    burnout_risk: int


class AiInsight(BaseModel):
    """AI-generated insight about a user's wellness trajectory."""

    insight: str
    trend: str
    risk_level: str


class EmployeeSummary(BaseModel):
    """Per-employee summary visible to managers."""

    user_id: uuid.UUID
    name: str
    entries: int
    avg_mood: float
    avg_stress: float
    avg_burnout: float
    latest_sentiment: str | None
    burnout_risk_level: str


class ManagerDashboard(BaseModel):
    """Aggregated view for managers across their organization."""

    company: str
    total_employees: int
    total_entries: int
    avg_mood: float
    avg_stress: float
    avg_burnout: float
    burnout_high_count: int
    burnout_medium_count: int
    burnout_low_count: int
    top_recommendations: list[str]
    employee_summaries: list[EmployeeSummary]
