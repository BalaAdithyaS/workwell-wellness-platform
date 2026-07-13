from unittest import result

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy import select
from app.database.db import SessionLocal
from app.models.wellness import WellnessEntry
from app.models.user import User

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.get("/all-employees")
def get_all_employees(
    team_id: str,
    db: Session = Depends(get_db)
):
    employees = (
        db.query(User)
        .filter(
            User.team_id == team_id,
            User.role == "employee"
        )
        .all()
    )

    result = []

    for employee in employees:

        latest_entry = (
            db.query(WellnessEntry)
            .filter(
                WellnessEntry.user_id == employee.id
            )
            .order_by(
                WellnessEntry.created_at.desc()
            )
            .first()
        )

        result.append({
            "name": employee.name,
            "email": employee.email,
            "mood_score": (
                latest_entry.mood_score
                if latest_entry
                else None
            ),
            "stress_level": (
                latest_entry.stress_level
                if latest_entry
                else None
            ),
            "burnout_risk": (
                latest_entry.burnout_risk
                if latest_entry
                else None
            ),
            "sentiment": (
                latest_entry.sentiment
                if latest_entry
                else "No data"
            )
        })

    return result
@router.get("/recent-submissions")
def recent_submissions(db: Session = Depends(get_db)):

    entries = (
        db.query(
            User.name,
            WellnessEntry.created_at,
            WellnessEntry.mood_score,
            WellnessEntry.stress_level
        )
        .join(
            User,
            WellnessEntry.user_id == User.id
        )
        .order_by(WellnessEntry.created_at.desc())
        .limit(10)
        .all()
    )

    result = []

    for e in entries:
        result.append({
            "name": e.name,
            "date": e.created_at.strftime("%d/%m/%Y"),
            "mood": e.mood_score,
            "stress": e.stress_level
        })

    return result
@router.get("/summary/{user_id}")
def get_summary(
    user_id: str,
    db: Session = Depends(get_db)
):

    entries = db.query(WellnessEntry).filter(
        WellnessEntry.user_id == user_id
    )

    avg_mood = entries.with_entities(
        func.avg(WellnessEntry.mood_score)
    ).scalar()

    avg_stress = entries.with_entities(
        func.avg(WellnessEntry.stress_level)
    ).scalar()

    avg_burnout = entries.with_entities(
        func.avg(WellnessEntry.burnout_risk)
    ).scalar()

    total_entries = entries.count()

    return {
        "average_mood": round(avg_mood or 0, 1),
        "average_stress": round(avg_stress or 0, 1),
        "average_burnout": round(avg_burnout or 0, 1),
        "total_entries": total_entries
    }
@router.get("/ai-insight/{user_id}")
def get_ai_insight(
    user_id: str,
    db: Session = Depends(get_db)
):
    latest_entry = (
        db.query(WellnessEntry)
        .filter(
            WellnessEntry.user_id == user_id
        )
        .order_by(
            WellnessEntry.created_at.desc()
        )
        .first()
    )

    if not latest_entry:
        return {
            "has_data": False,
            "sentiment": None,
            "recommendation": None
        }

    return {
        "has_data": True,
        "sentiment": latest_entry.sentiment,
        "recommendation": latest_entry.recommendation
    }

@router.get("/manager-summary")
def get_manager_summary(
    team_id: str,
    db: Session = Depends(get_db)
):

    team_entries = (
        db.query(WellnessEntry)
        .join(
            User,
            WellnessEntry.user_id == User.id
        )
        .filter(
            User.team_id == team_id
        )
    )

    total_employees = (
        db.query(
            func.count(func.distinct(User.id))
        )
        .filter(
            User.team_id == team_id
        )
        .scalar()
    )

    average_mood = team_entries.with_entities(
        func.avg(WellnessEntry.mood_score)
    ).scalar()

    average_stress = team_entries.with_entities(
        func.avg(WellnessEntry.stress_level)
    ).scalar()

    high_burnout = team_entries.filter(
        WellnessEntry.burnout_risk >= 4
    ).count()

    return {
        "total_employees": total_employees or 0,
        "average_mood": round(average_mood or 0, 1),
        "average_stress": round(average_stress or 0, 1),
        "high_burnout": high_burnout
    }

@router.get("/high-risk-employees")
def get_high_risk_employees(
    team_id: str,
    db: Session = Depends(get_db)
):
    employees = (
        db.query(
            WellnessEntry,
            User.name
        )
        .join(
            User,
            WellnessEntry.user_id == User.id
        )
        .filter(
            User.team_id == team_id,
            WellnessEntry.burnout_risk >= 4
        )
        .all()
    )

    result = []

    for wellness, name in employees:
        result.append({
            "name": name,
            "mood_score": wellness.mood_score,
            "stress_level": wellness.stress_level,
            "burnout_risk": wellness.burnout_risk,
            "sentiment": wellness.sentiment
        })

    return result
@router.get("/team-trends")
def get_team_trends(
    team_id: str,
    db: Session = Depends(get_db)
):

    entries = (
        db.query(WellnessEntry)
        .join(
            User,
            WellnessEntry.user_id == User.id
        )
        .filter(
            User.team_id == team_id
        )
        .order_by(
            WellnessEntry.created_at.asc()
        )
        .all()
    )

    result = []

    for entry in entries:
        result.append({
            "date": entry.created_at.strftime("%d/%m"),
            "mood": entry.mood_score,
            "stress": entry.stress_level,
            "burnout": entry.burnout_risk
        })

    return result