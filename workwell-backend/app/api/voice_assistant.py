from fastapi import APIRouter
import google.generativeai as genai
from app.services.gemini_service import analyze_wellness
import json
from datetime import datetime
from uuid import UUID

from app.database.db import SessionLocal
from app.models.voice_assessment import VoiceAssessment
from app.models.wellness import WellnessEntry

router = APIRouter()


@router.get("/start")
def start_conversation():

    return {
        "question": "How are you feeling today?"
    }


@router.post("/next-question")
def next_question(payload: dict):

    conversation = payload["conversation"]

    if len(conversation) >= 5:
        return {
            "done": True
        }

    prompt = f"""
You are an AI wellness coach.

Conversation:

{conversation}

Choose ONE question from these categories that has not been covered yet:

1. Workload
2. Stress
3. Sleep
4. Team Support
5. Work-Life Balance

Ask only ONE short question.

Maximum 15 words.
No advice.
No explanation.
"""

    model = genai.GenerativeModel(
        "gemini-2.5-flash"
    )

    response = model.generate_content(prompt)

    return {
        "question": response.text.strip()
    }


@router.post("/final-analysis")
def final_analysis(payload: dict):

    conversation = payload["conversation"]
    user_id = payload["user_id"]

    full_text = ""

    for item in conversation:
        full_text += f"""
Question: {item['question']}
Answer: {item['answer']}
"""

    result = analyze_wellness(full_text)

    db = SessionLocal()

    try:

        parsed = json.loads(result)

        print("========== GEMINI ==========")
        print(parsed)

        voice_assessment = VoiceAssessment(
            user_id=user_id,
            sentiment=parsed.get("sentiment", "neutral"),
            risk_level=parsed.get("risk_level", "Low"),
            recommendation=parsed.get(
                "recommendation",
                "No recommendation."
            )
        )

        db.add(voice_assessment)

        wellness_entry = WellnessEntry(
            user_id=UUID(user_id),
            mood_score=int(parsed.get("mood_score", 5)),
            stress_level=int(parsed.get("stress_level", 5)),
            burnout_risk=int(parsed.get("burnout_risk", 3)),
            sentiment=parsed.get("sentiment", "neutral"),
            recommendation=parsed.get(
                "recommendation",
                "No recommendation."
            ),
            notes="Voice Wellness Assessment"
        )

        db.add(wellness_entry)

        db.commit()

        print("VOICE ENTRY SAVED")

    except Exception as e:

        db.rollback()

        import traceback
        traceback.print_exc()

        raise e

    finally:

        db.close()

    return {
        "analysis": parsed
    }


@router.get("/status/{user_id}")
def get_status(user_id: str):

    db = SessionLocal()

    assessment = (
        db.query(VoiceAssessment)
        .filter(
            VoiceAssessment.user_id == user_id
        )
        .order_by(
            VoiceAssessment.created_at.desc()
        )
        .first()
    )

    if not assessment:
        db.close()
        return {
            "completed_today": False
        }

    today = datetime.utcnow().date()

    completed = (
        assessment.created_at.date() == today
    )

    db.close()

    return {
        "completed_today": completed
    }