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

        # Save Voice Assessment
        voice_assessment = VoiceAssessment(
            user_id=user_id,
            sentiment=parsed["sentiment"],
            risk_level=parsed["risk_level"],
            recommendation=parsed["recommendation"]
        )

        db.add(voice_assessment)

        # Save Wellness Entry for dashboard analytics
        wellness_entry = WellnessEntry(
            user_id=UUID(user_id),
            mood_score=parsed["mood_score"],
            stress_level=parsed["stress_level"],
            burnout_risk=parsed["burnout_risk"],
            sentiment=parsed["sentiment"],
            recommendation=parsed["recommendation"],
            notes="Voice Wellness Assessment"
        )

        db.add(wellness_entry)

        db.commit()

        db.refresh(voice_assessment)
        db.refresh(wellness_entry)

    except Exception as e:

        db.rollback()

        print("Voice Assessment Save Error:", e)

    finally:

        db.close()

    return {
        "analysis": result
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