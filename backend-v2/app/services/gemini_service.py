"""Google Gemini API integration for wellness analysis."""

import asyncio
import json
import logging
import re

import httpx

from app.core.config import get_settings
from app.schemas.voice import VoiceAnalysisResult, VoiceChatResponse

logger = logging.getLogger(__name__)

settings = get_settings()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

SYSTEM_PROMPT = """You are a wellness analysis AI. Given a user's voice conversation transcript about their mental health and work wellness, extract structured data.

Return ONLY a JSON object with these exact fields (no markdown, no code fences, just raw JSON):
{
  "mood_score": <integer 1-10, where 10 is excellent>,
  "stress_level": <integer 1-10, where 10 is very stressed>,
  "burnout_risk": <integer 1-10, where 10 is extreme burnout risk>,
  "sleep_hours": <number or null. Estimate nightly sleep in hours if mentioned, otherwise null>,
  "energy_level": <one of: "Very Low", "Low", "Moderate", "High", "Very High", or null if not inferable>,
  "sentiment": <one of: "positive", "negative", "neutral", "mixed">,
  "recommendation": <a concise 1-2 sentence personalized recommendation>,
  "summary": <a 2-3 sentence summary of the conversation>
}

Be empathetic but accurate in your assessment. Base scores on the user's own words. Only infer sleep_hours and energy_level if the user explicitly mentions them or they are clearly implied; otherwise return null."""

CHAT_SYSTEM_PROMPT = """You are a professional wellness coach having a warm, natural conversation with an employee. Your goal is to understand their current state across these wellness dimensions: mood, stress, sleep, energy, and work-life balance.

RULES:
- Ask ONLY ONE question at a time.
- Never ask about a topic the user has already addressed.
- Reference something specific the user said in your question to show you are listening.
- Keep questions conversational and supportive — never clinical or survey-like.
- If the user reveals multiple topics in one answer (e.g. sleep AND stress), acknowledge what they shared before moving to the next topic.
- After 4-6 total exchanges, or once you have enough information about mood, stress, sleep, and energy, signal completion.
- Vary your phrasing. Never start two consecutive questions the same way.

Based on the conversation so far, decide whether to ask another question or finish.

Return ONLY a JSON object (no markdown, no code fences):
{"next_question": "<your next question string, or null if done>", "done": false}
OR
{"next_question": null, "done": true}"""


def _call_gemini_sync(payload: dict) -> dict:
    """Synchronous Gemini call for use inside sync contexts."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            GEMINI_URL,
            params={"key": settings.GEMINI_API_KEY},
            json=payload,
        )
    response.raise_for_status()
    return response.json()


def _parse_gemini_json(data: dict) -> str:
    """Extract and clean the text from a Gemini response."""
    candidates = data.get("candidates")
    if not candidates:
        raise RuntimeError("Gemini returned no candidates")
    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    if not text.strip():
        raise RuntimeError("Gemini returned empty response text")
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()
    return text


async def analyze_transcript(transcript: str) -> VoiceAnalysisResult:
    """Send the transcript to Gemini and parse the structured response.

    Retries on 429 (rate limit) and 5xx (server errors) with exponential backoff.
    """
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\nTranscript:\n{transcript}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        },
    }

    max_retries = 3
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    GEMINI_URL,
                    params={"key": settings.GEMINI_API_KEY},
                    json=payload,
                )

            if response.status_code == 429 or response.status_code >= 500:
                wait = 2**attempt
                logger.warning(
                    "Gemini API %d, retrying in %ds (attempt %d/%d)",
                    response.status_code,
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
                continue

            response.raise_for_status()
            break

        except httpx.TimeoutException as exc:
            wait = 2**attempt
            logger.warning(
                "Gemini timeout, retrying in %ds (attempt %d/%d): %s",
                wait,
                attempt + 1,
                max_retries,
                exc,
            )
            last_error = exc
            await asyncio.sleep(wait)
            continue
    else:
        detail = f"Gemini API unavailable after {max_retries} retries"
        if last_error:
            detail += f": {last_error}"
        raise RuntimeError(detail)

    data = response.json()
    text = _parse_gemini_json(data)
    logger.debug("Gemini raw response: %s", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini JSON: %s\nRaw: %s", exc, text)
        raise RuntimeError(f"Gemini returned invalid JSON: {exc}") from exc

    for key in ("mood_score", "stress_level", "burnout_risk"):
        parsed[key] = max(1, min(10, int(parsed[key])))

    if parsed.get("sleep_hours") is not None:
        parsed["sleep_hours"] = max(0.0, min(24.0, float(parsed["sleep_hours"])))
    if parsed.get("energy_level") is not None:
        valid_levels = {"Very Low", "Low", "Moderate", "High", "Very High"}
        if parsed["energy_level"] not in valid_levels:
            parsed["energy_level"] = None

    return VoiceAnalysisResult(**parsed)


async def generate_next_question(
    conversation: list[dict[str, str]],
) -> VoiceChatResponse:
    """Generate the next coaching question based on conversation history.

    Uses Gemini to produce a contextual, conversational follow-up.
    Returns VoiceChatResponse with next_question or done=True.
    """
    history_text = "\n".join(
        f"{'Coach' if m['role'] == 'coach' else 'User'}: {m['content']}"
        for m in conversation
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"{CHAT_SYSTEM_PROMPT}\n\nConversation so far:\n{history_text}"
                    }
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 256,
        },
    }

    max_retries = 2
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            data = await asyncio.to_thread(_call_gemini_sync, payload)
            text = _parse_gemini_json(data)
            parsed = json.loads(text)
            return VoiceChatResponse(
                next_question=parsed.get("next_question"),
                done=parsed.get("done", parsed.get("next_question") is None),
            )
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Gemini chat question gen failed (attempt %d/%d): %s",
                attempt + 1,
                max_retries,
                exc,
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)

    logger.error("Question generation failed after retries: %s", last_error)
    raise RuntimeError(f"Could not generate next question: {last_error}")
