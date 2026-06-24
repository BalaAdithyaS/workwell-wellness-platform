from app.services.gemini_service import analyze_wellness
import json

from sqlalchemy import select
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.wellness import WellnessEntry
from app.schemas.wellness_schema import WellnessCreate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/submit")
def submit_wellness(
    data: WellnessCreate,
    db: Session = Depends(get_db)
):

    try:
        ai_response = analyze_wellness(data.notes)

        print("Gemini Response:")
        print(ai_response)

        cleaned_response = (
            ai_response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        analysis = json.loads(cleaned_response)

        sentiment = analysis.get(
            "sentiment",
            "Neutral"
        )

        recommendation = analysis.get(
            "recommendation",
            "No recommendation available."
        )

    except Exception as e:

        print("Gemini Error:", e)

        sentiment = "Neutral"

        recommendation = (
            "Unable to generate recommendation."
        )

    entry = WellnessEntry(
        user_id=data.user_id,

        mood_score=data.mood_score,

        stress_level=data.stress_level,

        burnout_risk=data.burnout_risk,

        notes=data.notes,

        sentiment=sentiment,

        recommendation=recommendation
    )

    db.add(entry)

    db.commit()

    db.refresh(entry)

    return {
        "message": "Wellness entry stored",
        "entry_id": str(entry.id),
        "sentiment": sentiment,
        "recommendation": recommendation
    }


@router.get("/history/{user_id}")
def get_wellness_history(
    user_id: str,
    db: Session = Depends(get_db)
):

    entries = db.execute(
        select(WellnessEntry).where(
            WellnessEntry.user_id == user_id
        )
    ).scalars().all()

    return entries