from fastapi import APIRouter
import google.generativeai as genai
from app.services.gemini_service import analyze_wellness
import json
from app.models.voice_assessment import VoiceAssessment
from app.database.db import SessionLocal
from datetime import datetime
router = APIRouter()

@router.get("/start")
def start_conversation():

    return {
        "question": "How are you feeling today?"
    }


@router.post("/next-question")
def next_question(payload: dict):

    conversation = payload["conversation"]

    # Stop after 5 questions
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

    response = model.generate_content(
        prompt
    )

    return {
        "question": response.text.strip()
    }


@router.post("/final-analysis")
def final_analysis(payload: dict):

    conversation = payload["conversation"]

    full_text = ""

    for item in conversation:

        full_text += f"""
Question: {item['question']}
Answer: {item['answer']}
"""

    result = analyze_wellness(full_text)

    try:

        parsed = json.loads(result)

        db = SessionLocal()

        assessment = VoiceAssessment(
    user_id="demo-user",
    sentiment=parsed["sentiment"],
    risk_level=parsed["risk_level"],
    recommendation=parsed["recommendation"]
)

        db.add(assessment)
        db.commit()

    except Exception as e:

        print("Voice Assessment Save Error:", e)

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
        return {
            "completed_today": False
        }

    today = datetime.utcnow().date()

    return {
        "completed_today":
        assessment.created_at.date() == today
    }