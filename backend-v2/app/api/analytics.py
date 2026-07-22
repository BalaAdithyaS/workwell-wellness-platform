"""Analytics endpoints — all read from WellnessEntry."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.schemas.analytics import AiInsight, ChartDataPoint, WellnessSummary
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=WellnessSummary)
def summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WellnessSummary:
    """Aggregated wellness statistics for the authenticated user."""
    return analytics_service.get_summary(db, current_user.id)


@router.get("/chart", response_model=list[ChartDataPoint])
def chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChartDataPoint]:
    """Wellness metrics over time for charting."""
    return analytics_service.get_chart_data(db, current_user.id)


@router.get("/ai-insight", response_model=AiInsight)
def ai_insight(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AiInsight:
    """AI-generated wellness insight based on recent entries."""
    return analytics_service.get_ai_insight(db, current_user.id)
