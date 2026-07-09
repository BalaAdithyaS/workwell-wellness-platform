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

@router.post("/seed")
def seed_teams(
    db: Session = Depends(get_db)
):
    default_teams = [
        {
            "team_id": "TEAM-001",
            "name": "Engineering",
            "description": "Software development and technical operations"
        },
        {
            "team_id": "TEAM-002",
            "name": "Human Resources",
            "description": "Employee management and people operations"
        },
        {
            "team_id": "TEAM-003",
            "name": "Finance",
            "description": "Finance and accounting operations"
        },
        {
            "team_id": "TEAM-004",
            "name": "Marketing",
            "description": "Marketing and communications"
        },
        {
            "team_id": "TEAM-005",
            "name": "Operations",
            "description": "Business and operational management"
        }
    ]

    created = 0

    for team_data in default_teams:
        existing_team = (
            db.query(Team)
            .filter(
                Team.team_id == team_data["team_id"]
            )
            .first()
        )

        if not existing_team:
            db.add(Team(**team_data))
            created += 1

    db.commit()

    return {
        "message": "Team master data seeded successfully",
        "teams_created": created
    }