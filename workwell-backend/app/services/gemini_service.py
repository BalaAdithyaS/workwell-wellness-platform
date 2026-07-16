import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def analyze_wellness(text: str):

    prompt = f"""
You are an AI wellness assistant.

Analyze the employee's responses and estimate their current wellness.

Return ONLY valid JSON.

Return this exact format:

{{
    "mood_score": 1,
    "stress_level": 1,
    "burnout_risk": 1,
    "sentiment": "positive",
    "risk_level": "Low",
    "recommendation": "Short recommendation under 40 words."
}}

Rules:

- mood_score must be an integer from 1 to 10.
- stress_level must be an integer from 1 to 10.
- burnout_risk must be an integer from 1 to 5.
- sentiment must be exactly one of:
  positive
  neutral
  negative
- risk_level must be exactly one of:
  Low
  Moderate
  High
- recommendation must be less than 40 words.
- Do NOT return markdown.
- Do NOT return explanations.
- Return JSON only.

Employee Conversation:

{text}
"""

    response = model.generate_content(prompt)

    result = response.text

    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    return result


print("Gemini service loaded successfully")