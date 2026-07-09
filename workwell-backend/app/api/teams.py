from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.team import Team


router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_teams(
    db: Session = Depends(get_db)
):
    teams = (
        db.query(Team)
        .order_by(Team.name.asc())
        .all()
    )

    return [
        {
            "team_id": team.team_id,
            "name": team.name,
            "description": team.description
        }
        for team in teams
    ]

