"""Wellness endpoints — form submissions and history."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.db import get_db
from app.models.user import User
from app.models.wellness import Source
from app.schemas.wellness import WellnessCreate, WellnessResponse
from app.services import wellness_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wellness", tags=["wellness"])


@router.post(
    "/create", response_model=WellnessResponse, status_code=status.HTTP_201_CREATED
)
def create_wellness(
    payload: WellnessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WellnessResponse:
    """Submit a wellness form entry."""
    return wellness_service.create_entry(
        db, current_user.id, payload, source=Source.FORM
    )


@router.get("/history", response_model=list[WellnessResponse])
def wellness_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[WellnessResponse]:
    """Return wellness entries for the authenticated user with pagination."""
    return wellness_service.get_history(db, current_user.id, skip=skip, limit=limit)


@router.delete("/delete/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wellness(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a wellness entry owned by the authenticated user."""
    deleted = wellness_service.delete_entry(db, current_user.id, entry_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found or not owned by you",
        )
