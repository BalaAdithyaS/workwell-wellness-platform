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

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):

    avg_mood = db.query(
        func.avg(WellnessEntry.mood_score)
    ).scalar()

    avg_stress = db.query(
        func.avg(WellnessEntry.stress_level)
    ).scalar()

    avg_burnout = db.query(
        func.avg(WellnessEntry.burnout_risk)
    ).scalar()

    total_entries = db.query(
        WellnessEntry
    ).count()

    return {
        "average_mood": avg_mood,
        "average_stress": avg_stress,
        "average_burnout": avg_burnout,
        "total_entries": total_entries
    }
@router.get("/ai-insight/{user_id}")
def get_ai_insight(
    user_id: str,
    db: Session = Depends(get_db)
):

    latest_entry = db.execute(
        select(WellnessEntry)
        .where(WellnessEntry.user_id == user_id)
        .order_by(WellnessEntry.created_at.desc())
    ).scalars().first()

    if not latest_entry:
        return {
            "sentiment": "Unknown",
            "recommendation": "No wellness data found."
        }

    return {
        "sentiment": latest_entry.sentiment,
        "recommendation": latest_entry.recommendation
    }
@router.get("/manager-summary")
def get_manager_summary(
    db: Session = Depends(get_db)
):

    total_employees = db.query(
        func.count(func.distinct(WellnessEntry.user_id))
    ).scalar()

    average_mood = db.query(
        func.avg(WellnessEntry.mood_score)
    ).scalar()

    average_stress = db.query(
        func.avg(WellnessEntry.stress_level)
    ).scalar()

    high_burnout = db.query(
        WellnessEntry
    ).filter(
        WellnessEntry.burnout_risk >= 4
    ).count()

    return {
        "total_employees": total_employees,
        "average_mood": round(average_mood or 0, 1),
        "average_stress": round(average_stress or 0, 1),
        "high_burnout": high_burnout
    }
@router.get("/high-risk-employees")
def get_high_risk_employees(
    db: Session = Depends(get_db)
):

    employees = db.query(
        WellnessEntry,
        User.name
    ).join(
        User,
        WellnessEntry.user_id == User.id
    ).filter(
        WellnessEntry.burnout_risk >= 4
    ).all()

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
    db: Session = Depends(get_db)
):

    entries = db.query(
        WellnessEntry
    ).order_by(
        WellnessEntry.created_at.asc()
    ).all()

    result = []

    for entry in entries:

        result.append({
            "date": entry.created_at.strftime("%d/%m"),
            "mood": entry.mood_score,
            "stress": entry.stress_level,
            "burnout": entry.burnout_risk
        })

    return result