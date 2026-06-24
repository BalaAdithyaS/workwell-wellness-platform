from pydantic import BaseModel

class WellnessCreate(BaseModel):

    user_id: str

    mood_score: int

    stress_level: int

    burnout_risk: int

    notes: str