"""Manager dashboard endpoint."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.database.db import get_db
from app.models.user import Role, User
from app.schemas.analytics import ManagerDashboard
from app.services.manager_service import get_manager_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manager", tags=["manager"])


@router.get("/dashboard", response_model=ManagerDashboard)
def dashboard(
    current_user: User = Depends(require_role(Role.manager)),
    db: Session = Depends(get_db),
) -> ManagerDashboard:
    """Organization-wide wellness dashboard — manager only."""
    return get_manager_dashboard(db, current_user)
