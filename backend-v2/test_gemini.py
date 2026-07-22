"""Test Gemini API directly."""

import httpx
from app.core.config import get_settings

settings = get_settings()

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

payload = {
    "contents": [{"role": "user", "parts": [{"text": "Say hello"}]}],
    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 256},
}

r = httpx.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload, timeout=30)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:1000]}")
