from fastapi import APIRouter
from pydantic import BaseModel

from app.services.gemini_service import analyze_wellness

router = APIRouter()

class VoiceRequest(BaseModel):
    text: str

@router.post("/voice-analysis")
def voice_analysis(data: VoiceRequest):

    result = analyze_wellness(data.text)

    return {
        "analysis": result
    }
@router.post("/analyze")
async def analyze(data: dict):

    result = analyze_wellness(
        data["text"]
    )

    return {
        "analysis": result
    }