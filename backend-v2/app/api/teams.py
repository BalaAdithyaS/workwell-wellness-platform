"""Teams endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.team import Team
from app.schemas.team import TeamResponse

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=list[TeamResponse])
def list_teams(db: Session = Depends(get_db)) -> list[TeamResponse]:
    """Return all teams."""
    rows = db.execute(select(Team).order_by(Team.name)).scalars().all()
    return [TeamResponse.model_validate(r) for r in rows]
