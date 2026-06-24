import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_wellness(text: str):

    prompt = f"""
Analyze the following employee wellness note.

Return JSON only.

Recommendation must be under 25 words.

{{
    "sentiment": "",
    "risk_level": "",
    "recommendation": ""
}}

Note:
{text}
"""

    response = model.generate_content(prompt)

    result = response.text

    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    return result

print("Gemini service loaded successfully")