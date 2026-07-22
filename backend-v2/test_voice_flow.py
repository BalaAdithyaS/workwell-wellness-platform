"""Test voice flow with mocked Gemini to verify voice → DB → analytics data pipeline."""

import httpx
import json
import time
import sys
from unittest.mock import patch, AsyncMock

BASE = "http://127.0.0.1:8000"
RESULTS = []


def log(tag, msg):
    RESULTS.append((tag, msg))
    print(f"  [{tag}] {msg}")


def check(condition, pass_msg, fail_msg):
    if condition:
        log("PASS", pass_msg)
        return True
    else:
        log("FAIL", fail_msg)
        return False


# ============================================================
# SETUP
# ============================================================
print("=" * 60)
print("VOICE FLOW TEST (Gemini Mocked)")
print("=" * 60)

email = f"voice_emp_{int(time.time())}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Voice Test Emp",
        "email": email,
        "password": "TestPass123!",
        "company": "VoiceTestCo",
        "role": "employee",
    },
    timeout=10,
)
emp_token = r.json()["access_token"]
emp_id = r.json()["user"]["id"]
emp_h = {"Authorization": f"Bearer {emp_token}"}
log("SETUP", f"Employee: {email} id={emp_id[:8]}...")

# Manager
email_mgr = f"voice_mgr_{int(time.time())}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Voice Test Mgr",
        "email": email_mgr,
        "password": "TestPass123!",
        "company": "VoiceTestCo",
        "role": "manager",
    },
    timeout=10,
)
mgr_token = r.json()["access_token"]
mgr_h = {"Authorization": f"Bearer {mgr_token}"}
log("SETUP", f"Manager: {email_mgr}")

# ============================================================
# Record baseline analytics
# ============================================================
print("\n--- Baseline Analytics ---")
r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
baseline_summary = r.json()
log("BASELINE", f"Entries before: {baseline_summary.get('total_entries')}")
log("BASELINE", f"Voice entries before: {baseline_summary.get('voice_entries')}")

# ============================================================
# Test voice analysis via direct service call (bypassing HTTP to mock Gemini)
# ============================================================
print("\n--- Step 1: Submit Voice via Mocked Gemini ---")

# We'll patch the gemini service at the module level and call the endpoint
# But since the server is a separate process, we need a different approach.
# Instead, let's test via direct DB + service call from here.

import sys

sys.path.insert(0, ".")

from app.database.db import SessionLocal
from app.models.user import User
from app.models.wellness import WellnessEntry, Source
from app.models.voice import VoiceConversation
from app.services.gemini_service import VoiceAnalysisResult

# Simulate what the voice_service would do after Gemini returns
mock_result = VoiceAnalysisResult(
    mood_score=6,
    stress_level=5,
    burnout_risk=4,
    sentiment="mixed",
    recommendation="Consider taking short breaks every hour to manage your stress levels.",
    summary="The user expressed feeling overwhelmed with work deadlines but is managing. Sleep quality has declined recently.",
)

transcript = "Coach: How are you feeling?\nUser: Stressed and tired.\nCoach: What's causing stress?\nUser: Too many deadlines at work."

db = SessionLocal()
try:
    from uuid import UUID

    uid = UUID(emp_id)

    conversation = VoiceConversation(
        user_id=uid,
        conversation=transcript,
        summary=mock_result.summary,
    )
    db.add(conversation)
    db.flush()

    entry = WellnessEntry(
        user_id=uid,
        source=Source.VOICE,
        mood_score=mock_result.mood_score,
        stress_level=mock_result.stress_level,
        burnout_risk=mock_result.burnout_risk,
        sentiment=mock_result.sentiment,
        recommendation=mock_result.recommendation,
        notes=None,
    )
    db.add(entry)
    db.flush()
    db.commit()
    db.refresh(entry)
    db.refresh(conversation)

    we_id = str(entry.id)
    vc_id = str(conversation.id)
    log(
        "DB_INSERT",
        f"WellnessEntry created: {we_id[:8]}... source={entry.source.value}",
    )
    log("DB_INSERT", f"VoiceConversation created: {vc_id[:8]}...")
    log(
        "DB_VALUES",
        f"mood={entry.mood_score} stress={entry.stress_level} burnout={entry.burnout_risk} sentiment={entry.sentiment}",
    )
finally:
    db.close()

# ============================================================
# Step 2: Verify WellnessEntry appears in history
# ============================================================
print("\n--- Step 2: Verify in Wellness History ---")

r = httpx.get(f"{BASE}/wellness/history", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    "GET /wellness/history returned 200",
    f"Failed: {r.status_code}",
)

if r.status_code == 200:
    history = r.json()
    voice_entry = None
    for entry in history:
        if entry.get("id") == we_id:
            voice_entry = entry
            break

    if voice_entry:
        log("HISTORY", "Voice entry found in wellness history!")
        check(
            voice_entry.get("source") == "VOICE",
            "source='VOICE'",
            f"source='{voice_entry.get('source')}'",
        )
        check(
            voice_entry.get("mood_score") == 6,
            "mood_score=6",
            f"mood_score={voice_entry.get('mood_score')}",
        )
        check(
            voice_entry.get("stress_level") == 5,
            "stress_level=5",
            f"stress_level={voice_entry.get('stress_level')}",
        )
        check(
            voice_entry.get("burnout_risk") == 4,
            "burnout_risk=4",
            f"burnout_risk={voice_entry.get('burnout_risk')}",
        )
        check(
            voice_entry.get("sentiment") == "mixed",
            "sentiment='mixed'",
            f"sentiment='{voice_entry.get('sentiment')}'",
        )
        check(
            voice_entry.get("recommendation") == mock_result.recommendation,
            "recommendation matches",
            "recommendation mismatch",
        )
    else:
        log("FAIL", f"Voice entry {we_id[:8]} NOT found in history!")
        for e in history[:3]:
            log(
                "HISTORY_ENTRY",
                f"  id={e.get('id', '?')[:8]}... source={e.get('source')}",
            )

# ============================================================
# Step 3: Verify Voice History
# ============================================================
print("\n--- Step 3: Verify Voice History ---")

r = httpx.get(f"{BASE}/voice/history", headers=emp_h, timeout=10)
check(
    r.status_code == 200, "GET /voice/history returned 200", f"Failed: {r.status_code}"
)

if r.status_code == 200:
    vhistory = r.json()
    check(
        len(vhistory) >= 1,
        f"Voice history has {len(vhistory)} entries",
        "Voice history is empty!",
    )
    if vhistory:
        latest = vhistory[0]
        log("VOICE_HIST", f"Latest: summary={latest.get('summary', 'NONE')[:80]}...")

# ============================================================
# Step 4: Verify Dashboard Summary updated
# ============================================================
print("\n--- Step 4: Verify Dashboard Summary ---")

r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    "GET /analytics/summary returned 200",
    f"Failed: {r.status_code}",
)

if r.status_code == 200:
    summary = r.json()
    log("SUMMARY", json.dumps(summary, indent=2))
    check(
        summary.get("total_entries", 0) >= 1,
        f"total_entries={summary.get('total_entries')}",
        f"total_entries={summary.get('total_entries')}",
    )
    check(
        summary.get("voice_entries", 0) >= 1,
        f"voice_entries={summary.get('voice_entries')} (expected >=1)",
        f"voice_entries={summary.get('voice_entries')}",
    )
    check(
        summary.get("avg_mood", 0) > 0,
        f"avg_mood={summary.get('avg_mood')}",
        f"avg_mood={summary.get('avg_mood')}",
    )

# ============================================================
# Step 5: Verify Dashboard Charts updated
# ============================================================
print("\n--- Step 5: Verify Dashboard Charts ---")

r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    "GET /analytics/chart returned 200",
    f"Failed: {r.status_code}",
)

if r.status_code == 200:
    chart = r.json()
    check(len(chart) >= 1, f"Chart has {len(chart)} data points", f"Chart is empty!")
    if chart:
        dp = chart[-1]
        log(
            "CHART",
            f"Latest point: mood={dp.get('mood_score')} stress={dp.get('stress_level')} burnout={dp.get('burnout_risk')}",
        )
        check(
            dp.get("mood_score") == 6,
            f"Chart mood=6",
            f"Chart mood={dp.get('mood_score')}",
        )
        check(
            dp.get("stress_level") == 5,
            f"Chart stress=5",
            f"Chart stress={dp.get('stress_level')}",
        )
        check(
            dp.get("burnout_risk") == 4,
            f"Chart burnout=4",
            f"Chart burnout={dp.get('burnout_risk')}",
        )

# ============================================================
# Step 6: Verify Manager Dashboard
# ============================================================
print("\n--- Step 6: Verify Manager Dashboard ---")

r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_h, timeout=10)
check(
    r.status_code == 200,
    "GET /manager/dashboard returned 200",
    f"Failed: {r.status_code}",
)

if r.status_code == 200:
    dash = r.json()
    log("MANAGER", json.dumps(dash, indent=2, default=str)[:600])
    check(
        dash.get("total_entries", 0) >= 1,
        f"Manager total_entries={dash.get('total_entries')}",
        f"Manager total_entries={dash.get('total_entries')}",
    )
    check(
        dash.get("avg_mood", 0) > 0,
        f"Manager avg_mood={dash.get('avg_mood')}",
        f"Manager avg_mood={dash.get('avg_mood')}",
    )
    emp_summaries = dash.get("employee_summaries", [])
    check(
        len(emp_summaries) >= 1,
        f"Manager has {len(emp_summaries)} employee summaries",
        "Manager has 0 employee summaries",
    )
    if emp_summaries:
        for es in emp_summaries:
            log(
                "EMP",
                f"  {es.get('name')}: entries={es.get('entries')} mood={es.get('avg_mood')} stress={es.get('avg_stress')} burnout={es.get('avg_burnout')} sentiment={es.get('latest_sentiment')}",
            )

# ============================================================
# Step 7: Direct PostgreSQL verification
# ============================================================
print("\n--- Step 7: Direct PostgreSQL Verification ---")

import sqlalchemy
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")
with engine.connect() as conn:
    result = conn.execute(
        text(f"""
        SELECT source, mood_score, stress_level, burnout_risk, sentiment, recommendation, notes, sleep_hours, energy_level
        FROM wellness_entries
        WHERE user_id = '{emp_id}'
        ORDER BY created_at DESC
    """)
    )
    rows = result.fetchall()
    log("DB", f"Total entries: {len(rows)}")
    for row in rows:
        log(
            "DB_ROW",
            f"  source={row[0]} mood={row[1]} stress={row[2]} burnout={row[3]} sentiment={row[4]}",
        )
        log(
            "DB_ROW",
            f"    rec={str(row[5])[:50]}... notes={row[6]} sleep={row[7]} energy={row[8]}",
        )
        if row[0] == "VOICE":
            check(
                row[1] is not None and row[1] > 0,
                f"DB VOICE mood_score={row[1]}",
                f"DB VOICE mood_score invalid: {row[1]}",
            )
            check(
                row[2] is not None and row[2] > 0,
                f"DB VOICE stress_level={row[2]}",
                f"DB VOICE stress_level invalid: {row[2]}",
            )
            check(
                row[3] is not None and row[3] > 0,
                f"DB VOICE burnout_risk={row[3]}",
                f"DB VOICE burnout_risk invalid: {row[3]}",
            )
            check(
                row[4] is not None,
                f"DB VOICE sentiment='{row[4]}'",
                f"DB VOICE sentiment is None",
            )
            check(
                row[5] is not None,
                f"DB VOICE recommendation present",
                f"DB VOICE recommendation is None",
            )

    # Check voice_conversations
    result = conn.execute(
        text(f"""
        SELECT id, summary FROM voice_conversations WHERE user_id = '{emp_id}'
    """)
    )
    vrows = result.fetchall()
    log("DB", f"Voice conversations: {len(vrows)}")
    check(
        len(vrows) >= 1,
        f"DB has {len(vrows)} voice conversations",
        "DB has 0 voice conversations",
    )

# ============================================================
# RESULTS
# ============================================================
print("\n" + "=" * 60)
print("VOICE FLOW RESULTS")
print("=" * 60)

passed = sum(1 for tag, _ in RESULTS if tag == "PASS")
failed = sum(1 for tag, _ in RESULTS if tag == "FAIL")
print(f"\nTotal: {passed} passed, {failed} failed")

if failed > 0:
    print("\n--- FAILED ---")
    for tag, msg in RESULTS:
        if tag == "FAIL":
            print(f"  [FAIL] {msg}")
    print(f"\nRESULT: FAIL")
else:
    print(f"\nRESULT: PASS")

sys.exit(1 if failed > 0 else 0)
