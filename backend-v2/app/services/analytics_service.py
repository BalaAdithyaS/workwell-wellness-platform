"""Analytics business logic — reads exclusively from WellnessEntry."""

import logging
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wellness import Source, WellnessEntry
from app.schemas.analytics import (
    AiInsight,
    ChartDataPoint,
    WellnessSummary,
)

logger = logging.getLogger(__name__)


def _burnout_level(score: int) -> str:
    """Classify burnout score into a human-readable risk level."""
    if score <= 3:
        return "low"
    if score <= 6:
        return "medium"
    return "high"


def get_summary(db: Session, user_id: uuid.UUID) -> WellnessSummary:
    """Aggregate wellness stats for a single user."""
    rows = (
        db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.user_id == user_id)
            .order_by(WellnessEntry.created_at.desc())
        )
        .scalars()
        .all()
    )

    if not rows:
        return WellnessSummary(
            total_entries=0,
            avg_mood=0.0,
            avg_stress=0.0,
            avg_burnout=0.0,
            latest_sentiment=None,
            form_entries=0,
            voice_entries=0,
        )

    total = len(rows)
    mood_avg = sum(r.mood_score for r in rows) / total
    stress_avg = sum(r.stress_level for r in rows) / total
    burnout_avg = sum(r.burnout_risk for r in rows) / total
    form_count = sum(1 for r in rows if r.source == Source.FORM)
    voice_count = sum(1 for r in rows if r.source == Source.VOICE)

    return WellnessSummary(
        total_entries=total,
        avg_mood=round(mood_avg, 2),
        avg_stress=round(stress_avg, 2),
        avg_burnout=round(burnout_avg, 2),
        latest_sentiment=rows[0].sentiment,
        form_entries=form_count,
        voice_entries=voice_count,
    )


def get_chart_data(db: Session, user_id: uuid.UUID) -> list[ChartDataPoint]:
    """Return wellness metrics over time for charting."""
    rows = (
        db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.user_id == user_id)
            .order_by(WellnessEntry.created_at.asc())
        )
        .scalars()
        .all()
    )

    return [
        ChartDataPoint(
            date=r.created_at,
            mood_score=r.mood_score,
            stress_level=r.stress_level,
            burnout_risk=r.burnout_risk,
        )
        for r in rows
    ]


def get_ai_insight(db: Session, user_id: uuid.UUID) -> AiInsight:
    """Generate a rule-based wellness insight from recent entries.

    This is deterministic and fast — no external API call needed.
    Could be extended to call Gemini for richer insights.
    """
    rows = (
        db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.user_id == user_id)
            .order_by(WellnessEntry.created_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )

    if not rows:
        return AiInsight(
            insight="No wellness data yet. Start by filling a form or having a voice session.",
            trend="stable",
            risk_level="low",
        )

    avg_mood = sum(r.mood_score for r in rows) / len(rows)
    avg_stress = sum(r.stress_level for r in rows) / len(rows)
    avg_burnout = sum(r.burnout_risk for r in rows) / len(rows)

    # Determine trend from first half vs second half
    mid = len(rows) // 2
    if mid > 0:
        older = rows[mid:]
        newer = rows[:mid]
        older_burnout = sum(r.burnout_risk for r in older) / len(older)
        newer_burnout = sum(r.burnout_risk for r in newer) / len(newer)
        delta = newer_burnout - older_burnout
        if delta < -1:
            trend = "improving"
        elif delta > 1:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "stable"

    risk = _burnout_level(int(avg_burnout))

    # Build insight text
    parts = []
    if avg_mood >= 7:
        parts.append("Your mood has been generally positive")
    elif avg_mood >= 4:
        parts.append("Your mood has been moderate")
    else:
        parts.append("Your mood has been low recently")

    if avg_stress >= 7:
        parts.append("and stress levels are high")
    elif avg_stress >= 4:
        parts.append("with moderate stress levels")
    else:
        parts.append("and stress is well-managed")

    if avg_burnout >= 7:
        parts.append(
            "— burnout risk is significant. Consider taking time off or speaking with a professional."
        )
    elif avg_burnout >= 4:
        parts.append(
            "— burnout risk is moderate. Regular breaks and self-care are recommended."
        )
    else:
        parts.append("— burnout risk is low. Keep up the healthy habits!")

    insight = ". ".join(parts) + "."

    return AiInsight(insight=insight, trend=trend, risk_level=risk)
