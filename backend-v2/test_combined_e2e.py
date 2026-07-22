"""Combined E2E test: Wellness Form + Voice Assistant -> all downstream flows."""

import httpx
import json
import time
import sys
import uuid as uuid_mod

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
print("=" * 70)
print("COMBINED E2E: WELLNESS FORM + VOICE ASSISTANT -> DASHBOARD/ANALYTICS")
print("=" * 70)

ts = int(time.time())
email_emp = f"combo_emp_{ts}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Combo Test Employee",
        "email": email_emp,
        "password": "TestPass123!",
        "company": "ComboTestCo",
        "role": "employee",
    },
    timeout=10,
)
assert r.status_code == 201, f"Signup failed: {r.status_code} {r.text}"
emp_token = r.json()["access_token"]
emp_id = r.json()["user"]["id"]
emp_h = {"Authorization": f"Bearer {emp_token}"}
log("SETUP", f"Employee: {email_emp} id={emp_id[:8]}...")

email_mgr = f"combo_mgr_{ts}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Combo Test Manager",
        "email": email_mgr,
        "password": "TestPass123!",
        "company": "ComboTestCo",
        "role": "manager",
    },
    timeout=10,
)
assert r.status_code == 201, f"Manager signup failed: {r.status_code} {r.text}"
mgr_token = r.json()["access_token"]
mgr_h = {"Authorization": f"Bearer {mgr_token}"}
log("SETUP", f"Manager: {email_mgr}")

# ============================================================
# PART A: WELLNESS FORM
# ============================================================
print("\n" + "=" * 70)
print("PART A: WELLNESS FORM SUBMISSION")
print("=" * 70)

WELLNESS = {
    "mood_score": 9,
    "stress_level": 2,
    "burnout_risk": 1,
    "sentiment": "positive",
    "recommendation": "Excellent mood! Keep maintaining your work-life balance.",
    "notes": "Great morning yoga session, productive standup, team is aligned.",
    "sleep_hours": 8.0,
    "energy_level": "Very High",
}

# A1: Submit form
print("\n--- A1: Submit Wellness Form ---")
r = httpx.post(f"{BASE}/wellness/create", json=WELLNESS, headers=emp_h, timeout=10)
check(
    r.status_code == 201,
    f"POST /wellness/create -> 201",
    f"POST /wellness/create -> {r.status_code}: {r.text[:200]}",
)
form_entry = r.json() if r.status_code == 201 else {}
form_id = form_entry.get("id")

# A2: Verify ALL fields in response
print("\n--- A2: Verify Response Fields ---")
check(
    form_entry.get("mood_score") == 9,
    "resp mood_score=9",
    f"resp mood_score={form_entry.get('mood_score')}",
)
check(
    form_entry.get("stress_level") == 2,
    "resp stress_level=2",
    f"resp stress_level={form_entry.get('stress_level')}",
)
check(
    form_entry.get("burnout_risk") == 1,
    "resp burnout_risk=1",
    f"resp burnout_risk={form_entry.get('burnout_risk')}",
)
check(
    form_entry.get("sentiment") == "positive",
    "resp sentiment='positive'",
    f"resp sentiment='{form_entry.get('sentiment')}'",
)
check(
    form_entry.get("recommendation") == WELLNESS["recommendation"],
    "resp recommendation matches",
    "resp recommendation mismatch",
)
check(
    form_entry.get("notes") == WELLNESS["notes"],
    "resp notes match",
    f"resp notes={form_entry.get('notes')!r}",
)
check(
    form_entry.get("sleep_hours") == 8.0,
    "resp sleep_hours=8.0",
    f"resp sleep_hours={form_entry.get('sleep_hours')}",
)
check(
    form_entry.get("energy_level") == "Very High",
    "resp energy_level='Very High'",
    f"resp energy_level='{form_entry.get('energy_level')}'",
)
check(
    form_entry.get("source") == "FORM",
    "resp source='FORM'",
    f"resp source='{form_entry.get('source')}'",
)

# A3: Verify in wellness history
print("\n--- A3: Verify in Wellness History ---")
r = httpx.get(f"{BASE}/wellness/history", headers=emp_h, timeout=10)
check(r.status_code == 200, "history -> 200", f"history -> {r.status_code}")
history = r.json() if r.status_code == 200 else []
found = next((e for e in history if e.get("id") == form_id), None)
if found:
    check(
        found["mood_score"] == 9,
        "history mood=9",
        f"history mood={found['mood_score']}",
    )
    check(
        found["stress_level"] == 2,
        "history stress=2",
        f"history stress={found['stress_level']}",
    )
    check(
        found["burnout_risk"] == 1,
        "history burnout=1",
        f"history burnout={found['burnout_risk']}",
    )
    check(
        found["notes"] == WELLNESS["notes"],
        "history notes match",
        "history notes mismatch",
    )
    check(
        found["sleep_hours"] == 8.0,
        "history sleep=8.0",
        f"history sleep={found['sleep_hours']}",
    )
    check(
        found["energy_level"] == "Very High",
        "history energy='Very High'",
        f"history energy='{found['energy_level']}'",
    )
else:
    log("FAIL", f"Form entry {form_id[:8]} NOT found in history!")

# A4: Dashboard summary
print("\n--- A4: Dashboard Summary ---")
r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
summary = r.json() if r.status_code == 200 else {}
check(
    summary.get("total_entries", 0) >= 1,
    f"summary total={summary.get('total_entries')}",
    f"summary total={summary.get('total_entries')}",
)
check(
    summary.get("form_entries", 0) >= 1,
    f"summary form_entries={summary.get('form_entries')}",
    f"summary form_entries={summary.get('form_entries')}",
)
check(
    summary.get("avg_mood", 0) == 9.0,
    f"summary avg_mood=9.0",
    f"summary avg_mood={summary.get('avg_mood')}",
)

# A5: Dashboard charts
print("\n--- A5: Dashboard Charts ---")
r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
chart = r.json() if r.status_code == 200 else []
check(
    len(chart) >= 1, f"chart has {len(chart)} points", f"chart has {len(chart)} points"
)
if chart:
    check(
        chart[-1]["mood_score"] == 9,
        "chart mood=9",
        f"chart mood={chart[-1].get('mood_score')}",
    )

# A6: AI Insight
print("\n--- A6: AI Insight ---")
r = httpx.get(f"{BASE}/analytics/ai-insight", headers=emp_h, timeout=10)
insight = r.json() if r.status_code == 200 else {}
check(
    len(insight.get("insight", "")) > 0,
    f"insight text present",
    f"insight empty: {insight}",
)
check(
    insight.get("risk_level") == "low",
    f"insight risk='low' (burnout=1)",
    f"insight risk='{insight.get('risk_level')}'",
)

# ============================================================
# PART B: VOICE ASSISTANT (mocked Gemini, inserted via DB)
# ============================================================
print("\n" + "=" * 70)
print("PART B: VOICE ASSISTANT DATA FLOW")
print("=" * 70)

# B1: Insert voice data the same way voice_service does
print("\n--- B1: Simulate Voice Analysis (same code path as voice_service) ---")

sys.path.insert(0, ".")
from app.database.db import SessionLocal
from app.models.user import User
from app.models.wellness import WellnessEntry, Source
from app.models.voice import VoiceConversation
from app.schemas.voice import VoiceAnalysisResult
from uuid import UUID

voice_result = VoiceAnalysisResult(
    mood_score=5,
    stress_level=7,
    burnout_risk=6,
    sentiment="negative",
    recommendation="Try the Pomodoro technique. Take 5-min breaks every 25 minutes.",
    summary="Employee reports high stress from project deadlines and poor sleep quality.",
)

transcript = (
    "Coach: How are you feeling today?\nUser: Honestly quite stressed. We have three deadlines this week.\n"
    "Coach: What's been causing the most stress?\nUser: The project backlog keeps growing and I can't catch up.\n"
    "Coach: How has your sleep been?\nUser: Terrible. I've been waking up at 3am worrying about work.\n"
    "Coach: Do you feel you have work-life balance?\nUser: Not at all. I worked 12 hours yesterday.\n"
    "Coach: What would help you most right now?\nUser: I need to learn to manage my time better and actually disconnect."
)

db = SessionLocal()
try:
    uid = UUID(emp_id)

    conversation = VoiceConversation(
        user_id=uid, conversation=transcript, summary=voice_result.summary
    )
    db.add(conversation)
    db.flush()

    voice_entry = WellnessEntry(
        user_id=uid,
        source=Source.VOICE,
        mood_score=voice_result.mood_score,
        stress_level=voice_result.stress_level,
        burnout_risk=voice_result.burnout_risk,
        sentiment=voice_result.sentiment,
        recommendation=voice_result.recommendation,
        notes=None,
    )
    db.add(voice_entry)
    db.flush()
    db.commit()
    db.refresh(voice_entry)
    db.refresh(conversation)

    ve_id = str(voice_entry.id)
    vc_id = str(conversation.id)
    log("VOICE_INSERT", f"WellnessEntry: {ve_id[:8]}... source=VOICE")
    log("VOICE_INSERT", f"VoiceConversation: {vc_id[:8]}...")
finally:
    db.close()

# B2: Verify voice entry in wellness history
print("\n--- B2: Voice Entry in Wellness History ---")
r = httpx.get(f"{BASE}/wellness/history", headers=emp_h, timeout=10)
history = r.json() if r.status_code == 200 else []
vfound = next((e for e in history if e.get("id") == ve_id), None)
if vfound:
    check(
        vfound["source"] == "VOICE",
        "voice entry source='VOICE'",
        f"source='{vfound['source']}'",
    )
    check(vfound["mood_score"] == 5, "voice mood=5", f"mood={vfound['mood_score']}")
    check(
        vfound["stress_level"] == 7,
        "voice stress=7",
        f"stress={vfound['stress_level']}",
    )
    check(
        vfound["burnout_risk"] == 6,
        "voice burnout=6",
        f"burnout={vfound['burnout_risk']}",
    )
    check(
        vfound["sentiment"] == "negative",
        "voice sentiment='negative'",
        f"sentiment='{vfound['sentiment']}'",
    )
    check(
        vfound["recommendation"] == voice_result.recommendation,
        "voice recommendation matches",
        "recommendation mismatch",
    )
else:
    log("FAIL", f"Voice entry {ve_id[:8]} NOT found in wellness history!")
    for e in history[:5]:
        log("DEBUG", f"  id={e.get('id', '?')[:8]} source={e.get('source')}")

# B3: Voice conversation history
print("\n--- B3: Voice Conversation History ---")
r = httpx.get(f"{BASE}/voice/history", headers=emp_h, timeout=10)
vhist = r.json() if r.status_code == 200 else []
check(len(vhist) >= 1, f"voice history has {len(vhist)} entries", "voice history empty")
if vhist:
    check(
        vhist[0].get("summary") == voice_result.summary,
        "voice summary matches",
        "voice summary mismatch",
    )

# B4: Dashboard summary (now has both form + voice)
print("\n--- B4: Dashboard Summary (form + voice) ---")
r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
summary = r.json() if r.status_code == 200 else {}
check(
    summary.get("total_entries", 0) >= 2,
    f"total_entries={summary.get('total_entries')} (>=2)",
    f"total_entries={summary.get('total_entries')}",
)
check(
    summary.get("voice_entries", 0) >= 1,
    f"voice_entries={summary.get('voice_entries')}",
    f"voice_entries={summary.get('voice_entries')}",
)
check(
    summary.get("form_entries", 0) >= 1,
    f"form_entries={summary.get('form_entries')}",
    f"form_entries={summary.get('form_entries')}",
)
# avg_mood = (9 + 5) / 2 = 7.0
check(
    summary.get("avg_mood", 0) == 7.0,
    f"avg_mood=7.0 ((9+5)/2)",
    f"avg_mood={summary.get('avg_mood')}",
)
check(
    summary.get("avg_stress", 0) == 4.5,
    f"avg_stress=4.5 ((2+7)/2)",
    f"avg_stress={summary.get('avg_stress')}",
)
check(
    summary.get("avg_burnout", 0) == 3.5,
    f"avg_burnout=3.5 ((1+6)/2)",
    f"avg_burnout={summary.get('avg_burnout')}",
)

# B5: Dashboard charts (should have 2 data points now)
print("\n--- B5: Dashboard Charts (2 data points) ---")
r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
chart = r.json() if r.status_code == 200 else []
check(
    len(chart) >= 2,
    f"chart has {len(chart)} points (>=2)",
    f"chart has {len(chart)} points",
)

# B6: AI Insight (should reflect combined data)
print("\n--- B6: AI Insight (combined) ---")
r = httpx.get(f"{BASE}/analytics/ai-insight", headers=emp_h, timeout=10)
insight = r.json() if r.status_code == 200 else {}
check(len(insight.get("insight", "")) > 0, "insight text present", "insight empty")
check(
    insight.get("risk_level") in ("low", "medium", "high"),
    f"risk_level='{insight.get('risk_level')}'",
    f"risk_level='{insight.get('risk_level')}'",
)
log(
    "INSIGHT",
    f"  trend={insight.get('trend')} risk={insight.get('risk_level')} text={insight.get('insight', '')[:80]}...",
)

# B7: Manager Dashboard
print("\n--- B7: Manager Dashboard ---")
r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_h, timeout=10)
dash = r.json() if r.status_code == 200 else {}
check(
    dash.get("total_entries", 0) >= 2,
    f"manager total_entries={dash.get('total_entries')}",
    f"manager total_entries={dash.get('total_entries')}",
)
check(
    dash.get("total_employees", 0) >= 1,
    f"manager employees={dash.get('total_employees')}",
    f"manager employees={dash.get('total_employees')}",
)
check(
    dash.get("avg_mood", 0) == 7.0,
    f"manager avg_mood=7.0",
    f"manager avg_mood={dash.get('avg_mood')}",
)
emp_sums = dash.get("employee_summaries", [])
our_emp = next((e for e in emp_sums if e.get("user_id") == emp_id), None)
if our_emp:
    check(
        our_emp["entries"] >= 2,
        f"emp entries={our_emp['entries']}",
        f"emp entries={our_emp['entries']}",
    )
    check(
        our_emp["avg_mood"] == 7.0,
        f"emp avg_mood=7.0",
        f"emp avg_mood={our_emp['avg_mood']}",
    )
    log(
        "MANAGER_EMP",
        f"  {our_emp['name']}: entries={our_emp['entries']} mood={our_emp['avg_mood']} stress={our_emp['avg_stress']} burnout={our_emp['avg_burnout']} sentiment={our_emp['latest_sentiment']}",
    )

# ============================================================
# PART C: DATABASE FIELD AUDIT
# ============================================================
print("\n" + "=" * 70)
print("PART C: DATABASE FIELD AUDIT")
print("=" * 70)

import sqlalchemy
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")
with engine.connect() as conn:
    # Check schema
    result = conn.execute(
        text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'wellness_entries'
        ORDER BY ordinal_position
    """)
    )
    cols = {row[0]: row[1] for row in result}
    required_cols = [
        "id",
        "user_id",
        "source",
        "mood_score",
        "stress_level",
        "burnout_risk",
        "sentiment",
        "recommendation",
        "notes",
        "created_at",
        "sleep_hours",
        "energy_level",
    ]
    for col in required_cols:
        check(
            col in cols,
            f"Column '{col}' exists ({cols.get(col, 'MISSING')})",
            f"Column '{col}' MISSING",
        )

    # Check FORM entry in DB
    print("\n--- FORM Entry DB Check ---")
    result = conn.execute(
        text(f"""
        SELECT mood_score, stress_level, burnout_risk, sentiment, recommendation, notes, sleep_hours, energy_level
        FROM wellness_entries WHERE id = :fid AND source = 'FORM'
    """),
        {"fid": uuid_mod.UUID(form_id)},
    )
    row = result.fetchone()
    if row:
        check(row[0] == 9, "DB FORM mood=9", f"DB FORM mood={row[0]}")
        check(row[1] == 2, "DB FORM stress=2", f"DB FORM stress={row[1]}")
        check(row[2] == 1, "DB FORM burnout=1", f"DB FORM burnout={row[2]}")
        check(
            row[3] == "positive",
            "DB FORM sentiment='positive'",
            f"DB FORM sentiment='{row[3]}'",
        )
        check(
            row[4] == WELLNESS["recommendation"],
            "DB FORM recommendation match",
            "DB FORM recommendation mismatch",
        )
        check(
            row[5] == WELLNESS["notes"],
            "DB FORM notes match",
            f"DB FORM notes={row[5]!r}",
        )
        check(row[6] == 8.0, "DB FORM sleep_hours=8.0", f"DB FORM sleep_hours={row[6]}")
        check(
            row[7] == "Very High",
            "DB FORM energy_level='Very High'",
            f"DB FORM energy_level='{row[7]}'",
        )
    else:
        log("FAIL", "FORM entry not found in DB!")

    # Check VOICE entry in DB
    print("\n--- VOICE Entry DB Check ---")
    result = conn.execute(
        text(f"""
        SELECT mood_score, stress_level, burnout_risk, sentiment, recommendation, notes, sleep_hours, energy_level
        FROM wellness_entries WHERE id = :vid AND source = 'VOICE'
    """),
        {"vid": uuid_mod.UUID(ve_id)},
    )
    row = result.fetchone()
    if row:
        check(row[0] == 5, "DB VOICE mood=5", f"DB VOICE mood={row[0]}")
        check(row[1] == 7, "DB VOICE stress=7", f"DB VOICE stress={row[1]}")
        check(row[2] == 6, "DB VOICE burnout=6", f"DB VOICE burnout={row[2]}")
        check(
            row[3] == "negative",
            "DB VOICE sentiment='negative'",
            f"DB VOICE sentiment='{row[3]}'",
        )
        check(
            row[4] == voice_result.recommendation,
            "DB VOICE recommendation match",
            "DB VOICE recommendation mismatch",
        )
    else:
        log("FAIL", "VOICE entry not found in DB!")

    # Check voice_conversations
    print("\n--- Voice Conversations DB Check ---")
    result = conn.execute(
        text(f"""
        SELECT conversation, summary FROM voice_conversations WHERE user_id = :uid
    """),
        {"uid": uuid_mod.UUID(emp_id)},
    )
    vrows = result.fetchall()
    check(
        len(vrows) >= 1,
        f"DB has {len(vrows)} voice conversations",
        "DB has 0 voice conversations",
    )
    if vrows:
        check(
            vrows[0][1] == voice_result.summary,
            "DB voice summary matches",
            "DB voice summary mismatch",
        )
        check(
            len(vrows[0][0]) > 50,
            f"DB conversation transcript length={len(vrows[0][0])}",
            "DB conversation transcript too short",
        )

# ============================================================
# FINAL RESULTS
# ============================================================
print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)

passed = sum(1 for tag, _ in RESULTS if tag == "PASS")
failed = sum(1 for tag, _ in RESULTS if tag == "FAIL")

print(f"\nTotal: {passed} passed, {failed} failed")

if failed > 0:
    print("\n--- FAILURES ---")
    for tag, msg in RESULTS:
        if tag == "FAIL":
            print(f"  [FAIL] {msg}")

# Category summary
print("\n--- CATEGORY SUMMARY ---")
categories = {
    "Wellness Form - Response": [
        m for t, m in RESULTS if t == "PASS" and "resp " in m.lower()
    ],
    "Wellness Form - History": [
        m for t, m in RESULTS if t == "PASS" and "history " in m.lower()
    ],
    "Wellness Form - Dashboard": [
        m
        for t, m in RESULTS
        if t == "PASS"
        and ("summary" in m.lower() or "chart" in m.lower() or "insight" in m.lower())
    ],
    "Voice - History": [
        m
        for t, m in RESULTS
        if t == "PASS"
        and "voice " in m.lower()
        and (
            "history" in m.lower()
            or "mood" in m.lower()
            or "stress" in m.lower()
            or "burnout" in m.lower()
            or "sentiment" in m.lower()
            or "recommendation" in m.lower()
        )
    ],
    "Voice - Dashboard": [
        m
        for t, m in RESULTS
        if t == "PASS" and "total_entries" in m.lower() and ">=2" in m.lower()
    ],
    "DB Audit": [
        m
        for t, m in RESULTS
        if t == "PASS"
        and (
            "column" in m.lower()
            or "db form" in m.lower()
            or "db voice" in m.lower()
            or "db has" in m.lower()
        )
    ],
    "Manager": [m for t, m in RESULTS if t == "PASS" and "manager" in m.lower()],
}
for cat, items in categories.items():
    status = "PASS" if all(True for _ in items) else "UNKNOWN"
    print(f"  {cat}: {len(items)} checks passed")

result = "FAIL" if failed > 0 else "PASS"
print(f"\n{'=' * 70}")
print(f"FINAL VERDICT: {result}")
print(f"{'=' * 70}")

sys.exit(1 if failed > 0 else 0)
