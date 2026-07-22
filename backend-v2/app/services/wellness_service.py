"""Wellness business logic."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.wellness import Source, WellnessEntry
from app.schemas.wellness import WellnessCreate, WellnessResponse

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


def create_entry(
    db: Session, user_id: uuid.UUID, payload: WellnessCreate, source: Source
) -> WellnessResponse:
    """Persist a wellness entry (form or voice-derived)."""
    entry = WellnessEntry(
        user_id=user_id,
        source=source,
        mood_score=payload.mood_score,
        stress_level=payload.stress_level,
        burnout_risk=payload.burnout_risk,
        sentiment=payload.sentiment,
        recommendation=payload.recommendation,
        notes=payload.notes,
        sleep_hours=payload.sleep_hours,
        energy_level=payload.energy_level,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    logger.info(
        "WellnessEntry created: id=%s user=%s source=%s",
        entry.id,
        user_id,
        source.value,
    )

    return WellnessResponse.model_validate(entry)


def get_history(
    db: Session,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
) -> list[WellnessResponse]:
    """Return wellness entries for a user, newest first, with pagination."""
    limit = min(limit, MAX_PAGE_SIZE)
    rows = (
        db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.user_id == user_id)
            .order_by(WellnessEntry.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [WellnessResponse.model_validate(r) for r in rows]


def get_history_all(db: Session, user_id: uuid.UUID) -> list[WellnessEntry]:
    """Return all wellness entries for a user (for analytics/manager aggregation)."""
    return (
        db.execute(
            select(WellnessEntry)
            .where(WellnessEntry.user_id == user_id)
            .order_by(WellnessEntry.created_at.desc())
        )
        .scalars()
        .all()
    )


def delete_entry(db: Session, user_id: uuid.UUID, entry_id: uuid.UUID) -> bool:
    """Delete a wellness entry owned by the user. Returns True if deleted."""
    entry = db.get(WellnessEntry, entry_id)

    if entry is None or entry.user_id != user_id:
        logger.warning("Delete failed: entry=%s user=%s", entry_id, user_id)
        return False

    db.delete(entry)
    db.commit()

    logger.info("WellnessEntry deleted: id=%s", entry_id)
    return True
