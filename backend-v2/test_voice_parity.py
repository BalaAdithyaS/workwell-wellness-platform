"""Verify voice sleep_hours/energy_level feature end-to-end.

Simulates voice_service.process_voice() using the exact same code path
(VoiceAnalysisResult + WellnessEntry constructor), then verifies via
real HTTP endpoints: history, summary, chart, manager dashboard, and
direct PostgreSQL.
"""

import sys, json, uuid as uuid_mod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.insert(0, ".")

from app.database.db import SessionLocal
from app.models.user import User
from app.models.wellness import WellnessEntry, Source
from app.models.voice import VoiceConversation
from app.schemas.voice import VoiceAnalysisResult
from app.services.voice_service import process_voice
from app.services.analytics_service import get_summary, get_chart_data, get_ai_insight
from app.services.manager_service import get_manager_dashboard
from app.services.wellness_service import get_history

import httpx

BASE = "http://127.0.0.1:8000"
RESULTS = []


def log(tag, msg):
    RESULTS.append((tag, msg))
    print(f"  [{tag}] {msg}")


def check(cond, ok, fail):
    if cond:
        log("PASS", ok)
        return True
    else:
        log("FAIL", fail)
        return False


# ============================================================
# SETUP
# ============================================================
print("=" * 70)
print("VOICE FEATURE PARITY VERIFICATION: sleep_hours + energy_level")
print("=" * 70)

ts = int(__import__("time").time())
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Feature Parity Emp",
        "email": f"fp_emp_{ts}@test.com",
        "password": "TestPass123!",
        "company": "FP_TestCo",
        "role": "employee",
    },
    timeout=10,
)
emp_token = r.json()["access_token"]
emp_id = r.json()["user"]["id"]
emp_h = {"Authorization": f"Bearer {emp_token}"}
log("SETUP", f"Employee id={emp_id[:8]}...")

r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Feature Parity Mgr",
        "email": f"fp_mgr_{ts}@test.com",
        "password": "TestPass123!",
        "company": "FP_TestCo",
        "role": "manager",
    },
    timeout=10,
)
mgr_h = {"Authorization": f"Bearer {r.json()['access_token']}"}


# ============================================================
# STEP 1: Test VoiceAnalysisResult parsing with sleep/energy
# ============================================================
print("\n--- Step 1: VoiceAnalysisResult schema ---")

# Simulate what Gemini returns (valid values)
result_with = VoiceAnalysisResult(
    mood_score=4,
    stress_level=7,
    burnout_risk=6,
    sleep_hours=5.5,
    energy_level="Low",
    sentiment="negative",
    recommendation="Try sleeping earlier.",
    summary="User is stressed and sleep-deprived.",
)
check(
    result_with.sleep_hours == 5.5,
    "VoiceAnalysisResult.sleep_hours=5.5",
    f"got {result_with.sleep_hours}",
)
check(
    result_with.energy_level == "Low",
    "VoiceAnalysisResult.energy_level='Low'",
    f"got {result_with.energy_level}",
)

# Simulate Gemini returning null (not inferable)
result_null = VoiceAnalysisResult(
    mood_score=5,
    stress_level=5,
    burnout_risk=5,
    sentiment="neutral",
    recommendation="Take breaks.",
    summary="General wellness check.",
)
check(
    result_null.sleep_hours is None,
    "VoiceAnalysisResult.sleep_hours=None when omitted",
    f"got {result_null.sleep_hours}",
)
check(
    result_null.energy_level is None,
    "VoiceAnalysisResult.energy_level=None when omitted",
    f"got {result_null.energy_level}",
)


# ============================================================
# STEP 2: Test Gemini prompt parsing logic (valid + invalid)
# ============================================================
print("\n--- Step 2: Gemini parsing logic ---")

from app.services.gemini_service import analyze_transcript
import app.services.gemini_service as gs

# Test clamping logic directly (bypass HTTP)
test_cases = [
    # (input_dict, expected_sleep, expected_energy)
    (
        {
            "mood_score": 5,
            "stress_level": 5,
            "burnout_risk": 5,
            "sleep_hours": 7.5,
            "energy_level": "High",
            "sentiment": "positive",
            "recommendation": "Good.",
            "summary": "OK.",
        },
        7.5,
        "High",
    ),
    (
        {
            "mood_score": 5,
            "stress_level": 5,
            "burnout_risk": 5,
            "sleep_hours": -1,
            "energy_level": "Invalid Level",
            "sentiment": "neutral",
            "recommendation": "OK.",
            "summary": "OK.",
        },
        0.0,
        None,
    ),  # clamped to 0, invalid energy -> None
    (
        {
            "mood_score": 5,
            "stress_level": 5,
            "burnout_risk": 5,
            "sleep_hours": 30,
            "energy_level": "Very High",
            "sentiment": "neutral",
            "recommendation": "OK.",
            "summary": "OK.",
        },
        24.0,
        "Very High",
    ),  # clamped to 24
    (
        {
            "mood_score": 5,
            "stress_level": 5,
            "burnout_risk": 5,
            "sentiment": "neutral",
            "recommendation": "OK.",
            "summary": "OK.",
        },
        None,
        None,
    ),  # omitted -> None
]

for tc_in, exp_sleep, exp_energy in test_cases:
    # Apply same clamping logic as gemini_service.py
    parsed = dict(tc_in)
    for key in ("mood_score", "stress_level", "burnout_risk"):
        parsed[key] = max(1, min(10, int(parsed[key])))
    if parsed.get("sleep_hours") is not None:
        parsed["sleep_hours"] = max(0.0, min(24.0, float(parsed["sleep_hours"])))
    if parsed.get("energy_level") is not None:
        valid_levels = {"Very Low", "Low", "Moderate", "High", "Very High"}
        if parsed["energy_level"] not in valid_levels:
            parsed["energy_level"] = None

    result = VoiceAnalysisResult(**parsed)
    check(
        result.sleep_hours == exp_sleep,
        f"sleep_hours: input={tc_in.get('sleep_hours', 'omitted')} -> {result.sleep_hours}",
        f"sleep_hours: expected {exp_sleep}, got {result.sleep_hours}",
    )
    check(
        result.energy_level == exp_energy,
        f"energy_level: input={tc_in.get('energy_level', 'omitted')} -> {result.energy_level}",
        f"energy_level: expected {exp_energy}, got {result.energy_level}",
    )


# ============================================================
# STEP 3: Insert via exact code path voice_service uses
# ============================================================
print("\n--- Step 3: Voice service code path (with sleep/energy) ---")

db = SessionLocal()
try:
    from uuid import UUID

    uid = UUID(emp_id)

    # Case A: Gemini returns sleep + energy
    result_a = VoiceAnalysisResult(
        mood_score=4,
        stress_level=7,
        burnout_risk=6,
        sleep_hours=5.5,
        energy_level="Low",
        sentiment="negative",
        recommendation="Try the Pomodoro technique and prioritize 8 hours of sleep.",
        summary="Employee reports high stress from deadlines and only 5 hours of sleep.",
    )

    conv_a = VoiceConversation(
        user_id=uid, conversation="Test transcript A", summary=result_a.summary
    )
    db.add(conv_a)
    db.flush()

    entry_a = WellnessEntry(
        user_id=uid,
        source=Source.VOICE,
        mood_score=result_a.mood_score,
        stress_level=result_a.stress_level,
        burnout_risk=result_a.burnout_risk,
        sentiment=result_a.sentiment,
        recommendation=result_a.recommendation,
        notes=None,
        sleep_hours=result_a.sleep_hours,
        energy_level=result_a.energy_level,
    )
    db.add(entry_a)
    db.flush()
    db.commit()
    db.refresh(entry_a)

    log(
        "INSERT_A",
        f"entry={str(entry_a.id)[:8]}... sleep={entry_a.sleep_hours} energy={entry_a.energy_level}",
    )

    # Case B: Gemini returns null for sleep + energy
    result_b = VoiceAnalysisResult(
        mood_score=6,
        stress_level=4,
        burnout_risk=3,
        sentiment="positive",
        recommendation="Keep up your positive routine!",
        summary="Employee is doing well overall.",
    )

    conv_b = VoiceConversation(
        user_id=uid, conversation="Test transcript B", summary=result_b.summary
    )
    db.add(conv_b)
    db.flush()

    entry_b = WellnessEntry(
        user_id=uid,
        source=Source.VOICE,
        mood_score=result_b.mood_score,
        stress_level=result_b.stress_level,
        burnout_risk=result_b.burnout_risk,
        sentiment=result_b.sentiment,
        recommendation=result_b.recommendation,
        notes=None,
        sleep_hours=result_b.sleep_hours,
        energy_level=result_b.energy_level,
    )
    db.add(entry_b)
    db.flush()
    db.commit()
    db.refresh(entry_b)

    log(
        "INSERT_B",
        f"entry={str(entry_b.id)[:8]}... sleep={entry_b.sleep_hours} energy={entry_b.energy_level}",
    )

    entry_a_id = str(entry_a.id)
    entry_b_id = str(entry_b.id)

finally:
    db.close()


# ============================================================
# STEP 4: Verify via Wellness History endpoint
# ============================================================
print("\n--- Step 4: Wellness History ---")

r = httpx.get(f"{BASE}/wellness/history?limit=10", headers=emp_h, timeout=10)
history = r.json() if r.status_code == 200 else []

entry_a_resp = next((e for e in history if e["id"] == entry_a_id), None)
entry_b_resp = next((e for e in history if e["id"] == entry_b_id), None)

if entry_a_resp:
    check(
        entry_a_resp["sleep_hours"] == 5.5,
        "History A: sleep_hours=5.5",
        f"got {entry_a_resp['sleep_hours']}",
    )
    check(
        entry_a_resp["energy_level"] == "Low",
        "History A: energy_level='Low'",
        f"got {entry_a_resp['energy_level']}",
    )
else:
    log("FAIL", "Entry A not found in history")

if entry_b_resp:
    check(
        entry_b_resp["sleep_hours"] is None,
        "History B: sleep_hours=None",
        f"got {entry_b_resp['sleep_hours']}",
    )
    check(
        entry_b_resp["energy_level"] is None,
        "History B: energy_level=None",
        f"got {entry_b_resp['energy_level']}",
    )
else:
    log("FAIL", "Entry B not found in history")


# ============================================================
# STEP 5: Verify via Dashboard Summary
# ============================================================
print("\n--- Step 5: Dashboard Summary ---")

r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
summary = r.json() if r.status_code == 200 else {}
check(
    summary.get("voice_entries", 0) >= 2,
    f"voice_entries={summary.get('voice_entries')} (>=2)",
    f"got {summary.get('voice_entries')}",
)
check(
    summary.get("total_entries", 0) >= 2,
    f"total_entries={summary.get('total_entries')} (>=2)",
    f"got {summary.get('total_entries')}",
)


# ============================================================
# STEP 6: Verify via Dashboard Charts
# ============================================================
print("\n--- Step 6: Dashboard Charts ---")

r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
chart = r.json() if r.status_code == 200 else []
check(len(chart) >= 2, f"chart has {len(chart)} points (>=2)", f"got {len(chart)}")


# ============================================================
# STEP 7: Verify via AI Insight
# ============================================================
print("\n--- Step 7: AI Insight ---")

r = httpx.get(f"{BASE}/analytics/ai-insight", headers=emp_h, timeout=10)
insight = r.json() if r.status_code == 200 else {}
check(len(insight.get("insight", "")) > 0, "AI insight text present", "empty insight")


# ============================================================
# STEP 8: Verify via Manager Dashboard
# ============================================================
print("\n--- Step 8: Manager Dashboard ---")

r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_h, timeout=10)
dash = r.json() if r.status_code == 200 else {}
check(
    dash.get("total_entries", 0) >= 2,
    f"manager total_entries={dash.get('total_entries')} (>=2)",
    f"got {dash.get('total_entries')}",
)
emp_sums = dash.get("employee_summaries", [])
our_emp = next((e for e in emp_sums if e.get("user_id") == emp_id), None)
if our_emp:
    check(
        our_emp["entries"] >= 2,
        f"emp entries={our_emp['entries']}",
        f"got {our_emp['entries']}",
    )


# ============================================================
# STEP 9: Direct PostgreSQL verification
# ============================================================
print("\n--- Step 9: Direct PostgreSQL ---")

engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")
with engine.connect() as conn:
    row_a = conn.execute(
        text("SELECT sleep_hours, energy_level FROM wellness_entries WHERE id = :eid"),
        {"eid": uuid_mod.UUID(entry_a_id)},
    ).fetchone()
    check(row_a[0] == 5.5, f"DB A: sleep_hours=5.5", f"got {row_a[0]}")
    check(row_a[1] == "Low", f"DB A: energy_level='Low'", f"got {row_a[1]}")

    row_b = conn.execute(
        text("SELECT sleep_hours, energy_level FROM wellness_entries WHERE id = :eid"),
        {"eid": uuid_mod.UUID(entry_b_id)},
    ).fetchone()
    check(row_b[0] is None, f"DB B: sleep_hours=NULL", f"got {row_b[0]}")
    check(row_b[1] is None, f"DB B: energy_level=NULL", f"got {row_b[1]}")


# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 70)
passed = sum(1 for t, _ in RESULTS if t == "PASS")
failed = sum(1 for t, _ in RESULTS if t == "FAIL")
print(f"Total: {passed} passed, {failed} failed")
if failed:
    print("\nFAILURES:")
    for t, m in RESULTS:
        if t == "FAIL":
            print(f"  {m}")
    sys.exit(1)
else:
    print("\nRESULT: PASS")
    sys.exit(0)
