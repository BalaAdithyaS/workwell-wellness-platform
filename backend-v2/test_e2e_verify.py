"""End-to-end verification of the original bug fix:
Wellness Form + Voice Assistant data must flow into dashboard/history/analytics.
"""

import httpx
import json
import time
import sys
from datetime import datetime, timezone

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
# SETUP: Create test users and get tokens
# ============================================================
print("=" * 60)
print("TEST 1: WELLNESS FORM DATA FLOW")
print("=" * 60)

# Employee signup/login
email_emp = f"e2e_emp_{int(time.time())}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "E2E Employee",
        "email": email_emp,
        "password": "TestPass123!",
        "company": "E2E_TestCo",
        "role": "employee",
    },
    timeout=10,
)
if r.status_code == 201:
    emp_token = r.json()["access_token"]
    emp_id = r.json()["user"]["id"]
    log("SETUP", f"Employee created: {email_emp} (id={emp_id[:8]}...)")
else:
    print(f"FATAL: Cannot create employee: {r.status_code} {r.text}")
    sys.exit(1)

# Manager signup/login
email_mgr = f"e2e_mgr_{int(time.time())}@test.com"
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "E2E Manager",
        "email": email_mgr,
        "password": "TestPass123!",
        "company": "E2E_TestCo",
        "role": "manager",
    },
    timeout=10,
)
if r.status_code == 201:
    mgr_token = r.json()["access_token"]
    mgr_id = r.json()["user"]["id"]
    log("SETUP", f"Manager created: {email_mgr} (id={mgr_id[:8]}...)")
else:
    print(f"FATAL: Cannot create manager: {r.status_code} {r.text}")
    sys.exit(1)

emp_h = {"Authorization": f"Bearer {emp_token}"}
mgr_h = {"Authorization": f"Bearer {mgr_token}"}

# ============================================================
# STEP 1: Submit Wellness Form with ALL unique values
# ============================================================
print("\n--- Step 1: Submit Wellness Form ---")

WELLNESS_PAYLOAD = {
    "mood_score": 8,
    "stress_level": 3,
    "burnout_risk": 2,
    "sentiment": "positive",
    "recommendation": "Keep up the great work! Your mood is high and stress is manageable.",
    "notes": "Had a productive meeting today. Feeling optimistic about the project deadline.",
    "sleep_hours": 7.5,
    "energy_level": "High",
}

r = httpx.post(
    f"{BASE}/wellness/create", json=WELLNESS_PAYLOAD, headers=emp_h, timeout=10
)
check(
    r.status_code == 201,
    f"POST /wellness/create returned 201",
    f"POST /wellness/create returned {r.status_code}: {r.text[:200]}",
)

if r.status_code == 201:
    created = r.json()
    entry_id = created.get("id")
    log(
        "RESPONSE", f"Created entry id={entry_id[:8]}... source={created.get('source')}"
    )

    # Check every field in the response
    check(
        created.get("mood_score") == 8,
        "Response mood_score=8",
        f"Response mood_score={created.get('mood_score')} (expected 8)",
    )
    check(
        created.get("stress_level") == 3,
        "Response stress_level=3",
        f"Response stress_level={created.get('stress_level')} (expected 3)",
    )
    check(
        created.get("burnout_risk") == 2,
        "Response burnout_risk=2",
        f"Response burnout_risk={created.get('burnout_risk')} (expected 2)",
    )
    check(
        created.get("sentiment") == "positive",
        f"Response sentiment='positive'",
        f"Response sentiment='{created.get('sentiment')}' (expected 'positive')",
    )
    check(
        created.get("recommendation") == WELLNESS_PAYLOAD["recommendation"],
        "Response recommendation matches",
        f"Response recommendation mismatch: {created.get('recommendation')[:50]}",
    )
    check(
        created.get("notes") == WELLNESS_PAYLOAD["notes"],
        "Response notes matches",
        f"Response notes={created.get('notes')!r}",
    )
    check(
        created.get("sleep_hours") == 7.5,
        f"Response sleep_hours=7.5",
        f"Response sleep_hours={created.get('sleep_hours')} (expected 7.5)",
    )
    check(
        created.get("energy_level") == "High",
        f"Response energy_level='High'",
        f"Response energy_level='{created.get('energy_level')}' (expected 'High')",
    )
    check(
        created.get("source") == "FORM",
        f"Response source='FORM'",
        f"Response source='{created.get('source')}' (expected 'FORM')",
    )

# ============================================================
# STEP 2: Verify in PostgreSQL via the history endpoint
# ============================================================
print("\n--- Step 2: Verify in Wellness History ---")

r = httpx.get(f"{BASE}/wellness/history", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /wellness/history returned 200",
    f"GET /wellness/history returned {r.status_code}",
)

if r.status_code == 200:
    history = r.json()
    check(
        len(history) >= 1, f"History has {len(history)} entries", f"History is empty!"
    )

    # Find our entry
    found = None
    for entry in history:
        if entry.get("id") == entry_id:
            found = entry
            break

    if found:
        log("DB_VERIFY", "Entry found in history")
        check(
            found.get("mood_score") == 8,
            "DB mood_score=8",
            f"DB mood_score={found.get('mood_score')}",
        )
        check(
            found.get("stress_level") == 3,
            "DB stress_level=3",
            f"DB stress_level={found.get('stress_level')}",
        )
        check(
            found.get("burnout_risk") == 2,
            "DB burnout_risk=2",
            f"DB burnout_risk={found.get('burnout_risk')}",
        )
        check(
            found.get("sentiment") == "positive",
            "DB sentiment='positive'",
            f"DB sentiment='{found.get('sentiment')}'",
        )
        check(
            found.get("recommendation") == WELLNESS_PAYLOAD["recommendation"],
            "DB recommendation matches",
            f"DB recommendation mismatch",
        )
        check(
            found.get("notes") == WELLNESS_PAYLOAD["notes"],
            "DB notes match",
            f"DB notes={found.get('notes')!r}",
        )
        check(
            found.get("sleep_hours") == 7.5,
            "DB sleep_hours=7.5",
            f"DB sleep_hours={found.get('sleep_hours')}",
        )
        check(
            found.get("energy_level") == "High",
            "DB energy_level='High'",
            f"DB energy_level='{found.get('energy_level')}'",
        )
        check(
            found.get("source") == "FORM",
            "DB source='FORM'",
            f"DB source='{found.get('source')}'",
        )
    else:
        log("FAIL", f"Entry {entry_id[:8]}... NOT found in history!")
        log("HISTORY", json.dumps(history[:2], indent=2, default=str)[:500])

# ============================================================
# STEP 3: Verify Dashboard Summary
# ============================================================
print("\n--- Step 3: Verify Dashboard Summary ---")

r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /analytics/summary returned 200",
    f"GET /analytics/summary returned {r.status_code}",
)

if r.status_code == 200:
    summary = r.json()
    log("SUMMARY", json.dumps(summary, indent=2))
    check(
        summary.get("total_entries", 0) >= 1,
        f"Summary total_entries={summary.get('total_entries')}",
        f"Summary total_entries={summary.get('total_entries')} (expected >=1)",
    )
    check(
        summary.get("avg_mood", 0) > 0,
        f"Summary avg_mood={summary.get('avg_mood')}",
        f"Summary avg_mood={summary.get('avg_mood')} (expected >0)",
    )
    check(
        summary.get("form_entries", 0) >= 1,
        f"Summary form_entries={summary.get('form_entries')}",
        f"Summary form_entries={summary.get('form_entries')} (expected >=1)",
    )

# ============================================================
# STEP 4: Verify Dashboard Charts
# ============================================================
print("\n--- Step 4: Verify Dashboard Charts ---")

r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /analytics/chart returned 200",
    f"GET /analytics/chart returned {r.status_code}",
)

if r.status_code == 200:
    chart = r.json()
    check(len(chart) >= 1, f"Chart has {len(chart)} data points", f"Chart is empty!")
    if chart:
        dp = chart[-1]  # most recent
        log("CHART", f"Latest data point: {json.dumps(dp, default=str)}")
        check(
            dp.get("mood_score") == 8,
            f"Chart mood_score=8",
            f"Chart mood_score={dp.get('mood_score')}",
        )
        check(
            dp.get("stress_level") == 3,
            f"Chart stress_level=3",
            f"Chart stress_level={dp.get('stress_level')}",
        )
        check(
            dp.get("burnout_risk") == 2,
            f"Chart burnout_risk=2",
            f"Chart burnout_risk={dp.get('burnout_risk')}",
        )

# ============================================================
# STEP 5: Verify AI Insight
# ============================================================
print("\n--- Step 5: Verify AI Insight ---")

r = httpx.get(f"{BASE}/analytics/ai-insight", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /analytics/ai-insight returned 200",
    f"GET /analytics/ai-insight returned {r.status_code}",
)

if r.status_code == 200:
    insight = r.json()
    log("INSIGHT", json.dumps(insight, indent=2))
    check(
        insight.get("insight", "") != "",
        "AI insight has text",
        f"AI insight is empty: {insight}",
    )
    check(
        insight.get("risk_level") in ("low", "medium", "high"),
        f"AI risk_level='{insight.get('risk_level')}'",
        f"AI risk_level invalid: {insight.get('risk_level')}",
    )
    check(
        insight.get("trend") in ("improving", "declining", "stable"),
        f"AI trend='{insight.get('trend')}'",
        f"AI trend invalid: {insight.get('trend')}",
    )

# ============================================================
# TEST 2: VOICE ASSISTANT DATA FLOW
# ============================================================
print("\n" + "=" * 60)
print("TEST 2: VOICE ASSISTANT DATA FLOW")
print("=" * 60)

# ============================================================
# STEP 6: Submit Voice Conversation
# ============================================================
print("\n--- Step 6: Submit Voice Conversation ---")

VOICE_TRANSCRIPT = """Coach: Hello! I'm your AI wellness coach. How are you feeling today? Tell me about your day.
User: I'm feeling pretty good today. Had a decent morning, though I'm a bit tired from staying up late last night working on a presentation.

Coach: What has been the biggest source of stress for you recently?
User: Definitely the upcoming product launch. There's a lot of pressure to get everything right before the deadline next week.

Coach: How well have you been sleeping? Any issues with rest?
User: Not great honestly. I've been averaging maybe 5 hours a night this week. I keep waking up thinking about work tasks.

Coach: Do you feel you have a good work-life balance right now?
User: Not really. I've been working late most nights and even checked emails over the weekend. I haven't had time for the gym in two weeks.

Coach: Is there anything specific you'd like help with or want to talk about?
User: I think I need help managing my time better. I want to learn to set boundaries between work and personal life. Also any tips for better sleep would be great."""

r = httpx.post(
    f"{BASE}/voice/analyze",
    json={"conversation": VOICE_TRANSCRIPT},
    headers=emp_h,
    timeout=60,
)
check(
    r.status_code == 201,
    f"POST /voice/analyze returned 201",
    f"POST /voice/analyze returned {r.status_code}: {r.text[:300]}",
)

if r.status_code == 201:
    voice_resp = r.json()
    log("VOICE_RESPONSE", json.dumps(voice_resp, indent=2, default=str)[:500])
    we_id = voice_resp.get("wellness_entry_id")
    vc_id = voice_resp.get("voice_conversation_id")
    log(
        "IDS",
        f"wellness_entry_id={we_id[:8] if we_id else 'MISSING'}... voice_conversation_id={vc_id[:8] if vc_id else 'MISSING'}...",
    )

    check(
        we_id is not None,
        "Voice response includes wellness_entry_id",
        "MISSING wellness_entry_id in voice response!",
    )
    check(
        vc_id is not None,
        "Voice response includes voice_conversation_id",
        "MISSING voice_conversation_id in voice response!",
    )
    check(
        voice_resp.get("mood_score") is not None,
        f"Voice mood_score={voice_resp.get('mood_score')}",
        f"Voice mood_score is None",
    )
    check(
        voice_resp.get("stress_level") is not None,
        f"Voice stress_level={voice_resp.get('stress_level')}",
        f"Voice stress_level is None",
    )
    check(
        voice_resp.get("burnout_risk") is not None,
        f"Voice burnout_risk={voice_resp.get('burnout_risk')}",
        f"Voice burnout_risk is None",
    )
    check(
        voice_resp.get("sentiment") is not None,
        f"Voice sentiment='{voice_resp.get('sentiment')}'",
        f"Voice sentiment is None",
    )
    check(
        voice_resp.get("recommendation") is not None,
        f"Voice recommendation present",
        f"Voice recommendation is None",
    )
    check(
        voice_resp.get("summary") is not None,
        f"Voice summary present",
        f"Voice summary is None",
    )
else:
    log("WARN", "Voice analysis failed - checking if it's a Gemini API issue")
    we_id = None
    vc_id = None

# ============================================================
# STEP 7: Verify WellnessEntry was created from voice
# ============================================================
print("\n--- Step 7: Verify WellnessEntry created from Voice ---")

if we_id:
    # Check via history - the voice entry should appear
    r = httpx.get(f"{BASE}/wellness/history", headers=emp_h, timeout=10)
    check(
        r.status_code == 200,
        f"GET /wellness/history returned 200",
        f"GET /wellness/history returned {r.status_code}",
    )

    if r.status_code == 200:
        history = r.json()
        voice_entry = None
        for entry in history:
            if entry.get("id") == we_id:
                voice_entry = entry
                break

        if voice_entry:
            log("DB_VERIFY", "Voice WellnessEntry found in wellness history!")
            check(
                voice_entry.get("source") == "VOICE",
                f"source='VOICE'",
                f"source='{voice_entry.get('source')}' (expected 'VOICE')",
            )
            check(
                voice_entry.get("mood_score") is not None
                and voice_entry.get("mood_score") > 0,
                f"mood_score={voice_entry.get('mood_score')}",
                f"mood_score invalid: {voice_entry.get('mood_score')}",
            )
            check(
                voice_entry.get("stress_level") is not None
                and voice_entry.get("stress_level") > 0,
                f"stress_level={voice_entry.get('stress_level')}",
                f"stress_level invalid: {voice_entry.get('stress_level')}",
            )
            check(
                voice_entry.get("burnout_risk") is not None
                and voice_entry.get("burnout_risk") > 0,
                f"burnout_risk={voice_entry.get('burnout_risk')}",
                f"burnout_risk invalid: {voice_entry.get('burnout_risk')}",
            )
            check(
                voice_entry.get("sentiment") is not None,
                f"sentiment='{voice_entry.get('sentiment')}'",
                f"sentiment is None",
            )
            check(
                voice_entry.get("recommendation") is not None,
                f"recommendation present",
                f"recommendation is None",
            )
        else:
            log(
                "FAIL",
                f"Voice WellnessEntry {we_id[:8]} NOT found in wellness history!",
            )
            # Show what IS in history
            for e in history[:5]:
                log(
                    "HISTORY_ENTRY",
                    f"  id={e.get('id', '?')[:8]}... source={e.get('source')} mood={e.get('mood_score')}",
                )
else:
    log("SKIP", "No wellness_entry_id from voice - cannot verify DB record")

# ============================================================
# STEP 8: Verify VoiceConversation was created
# ============================================================
print("\n--- Step 8: Verify VoiceConversation in Voice History ---")

r = httpx.get(f"{BASE}/voice/history", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /voice/history returned 200",
    f"GET /voice/history returned {r.status_code}",
)

if r.status_code == 200:
    vhistory = r.json()
    check(
        len(vhistory) >= 1,
        f"Voice history has {len(vhistory)} entries",
        f"Voice history is empty!",
    )
    if vhistory:
        latest = vhistory[0]
        log(
            "VOICE_HISTORY",
            f"Latest: id={latest.get('id', '?')[:8]}... summary={latest.get('summary', 'NONE')[:80]}...",
        )

# ============================================================
# STEP 9: Verify Dashboard Summary updated with voice data
# ============================================================
print("\n--- Step 9: Verify Dashboard Summary (after voice) ---")

r = httpx.get(f"{BASE}/analytics/summary", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /analytics/summary returned 200",
    f"GET /analytics/summary returned {r.status_code}",
)

if r.status_code == 200:
    summary = r.json()
    log("SUMMARY_AFTER_VOICE", json.dumps(summary, indent=2))
    check(
        summary.get("total_entries", 0) >= 2,
        f"total_entries={summary.get('total_entries')} (expected >=2)",
        f"total_entries={summary.get('total_entries')} (expected >=2)",
    )
    check(
        summary.get("voice_entries", 0) >= 1,
        f"voice_entries={summary.get('voice_entries')} (expected >=1)",
        f"voice_entries={summary.get('voice_entries')} (expected >=1)",
    )
    check(
        summary.get("form_entries", 0) >= 1,
        f"form_entries={summary.get('form_entries')} (expected >=1)",
        f"form_entries={summary.get('form_entries')} (expected >=1)",
    )

# ============================================================
# STEP 10: Verify Dashboard Charts updated
# ============================================================
print("\n--- Step 10: Verify Dashboard Charts (after voice) ---")

r = httpx.get(f"{BASE}/analytics/chart", headers=emp_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /analytics/chart returned 200",
    f"GET /analytics/chart returned {r.status_code}",
)

if r.status_code == 200:
    chart = r.json()
    check(
        len(chart) >= 2,
        f"Chart has {len(chart)} data points (expected >=2)",
        f"Chart has {len(chart)} data points (expected >=2)",
    )

# ============================================================
# STEP 11: Verify Manager Dashboard
# ============================================================
print("\n--- Step 11: Verify Manager Dashboard ---")

r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_h, timeout=10)
check(
    r.status_code == 200,
    f"GET /manager/dashboard returned 200",
    f"GET /manager/dashboard returned {r.status_code}",
)

if r.status_code == 200:
    dash = r.json()
    log("MANAGER_DASH", json.dumps(dash, indent=2, default=str)[:800])
    check(
        dash.get("total_entries", 0) >= 2,
        f"Manager total_entries={dash.get('total_entries')} (expected >=2)",
        f"Manager total_entries={dash.get('total_entries')}",
    )
    check(
        dash.get("total_employees", 0) >= 1,
        f"Manager total_employees={dash.get('total_employees')}",
        f"Manager total_employees={dash.get('total_employees')}",
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
        f"Manager has 0 employee summaries",
    )
    if emp_summaries:
        for es in emp_summaries:
            log(
                "EMP_SUMMARY",
                f"  {es.get('name')}: entries={es.get('entries')} mood={es.get('avg_mood')} stress={es.get('avg_stress')}",
            )

# ============================================================
# STEP 12: Direct DB verification via psycopg2/sqlalchemy
# ============================================================
print("\n--- Step 12: Direct PostgreSQL Verification ---")

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text

    engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")

    with engine.connect() as conn:
        # Check wellness_entries table structure
        result = conn.execute(
            text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'wellness_entries'
            ORDER BY ordinal_position
        """)
        )
        cols = result.fetchall()
        log("TABLE_SCHEMA", "wellness_entries columns:")
        for c in cols:
            log("SCHEMA", f"  {c[0]}: {c[1]} (nullable={c[2]})")

        # Check all entries for our user
        result = conn.execute(
            text(f"""
            SELECT id, user_id, source, mood_score, stress_level, burnout_risk,
                   sentiment, recommendation, notes, sleep_hours, energy_level, created_at
            FROM wellness_entries
            WHERE user_id = '{emp_id}'
            ORDER BY created_at DESC
        """)
        )
        rows = result.fetchall()
        log("DB_ENTRIES", f"Total entries for user: {len(rows)}")

        for row in rows:
            entry_id_short = str(row[0])[:8]
            log(
                "DB_ROW",
                f"  id={entry_id_short}... source={row[2]} mood={row[3]} stress={row[4]} burnout={row[5]} sentiment={row[6]}",
            )
            log(
                "DB_ROW",
                f"    recommendation={str(row[7])[:60]}... notes={row[8]} sleep={row[9]} energy={row[10]}",
            )

            # For the form entry, check ALL fields
            if row[2] == "FORM":
                check(
                    row[3] == 8,
                    f"DB FORM: mood_score=8",
                    f"DB FORM: mood_score={row[3]}",
                )
                check(
                    row[4] == 3,
                    f"DB FORM: stress_level=3",
                    f"DB FORM: stress_level={row[4]}",
                )
                check(
                    row[5] == 2,
                    f"DB FORM: burnout_risk=2",
                    f"DB FORM: burnout_risk={row[5]}",
                )
                check(
                    row[6] == "positive",
                    f"DB FORM: sentiment='positive'",
                    f"DB FORM: sentiment='{row[6]}'",
                )
                check(
                    row[7] == WELLNESS_PAYLOAD["recommendation"],
                    f"DB FORM: recommendation matches",
                    f"DB FORM: recommendation mismatch",
                )
                check(
                    row[8] == WELLNESS_PAYLOAD["notes"],
                    f"DB FORM: notes match",
                    f"DB FORM: notes='{row[8]}'",
                )
                check(
                    row[9] == 7.5,
                    f"DB FORM: sleep_hours=7.5",
                    f"DB FORM: sleep_hours={row[9]}",
                )
                check(
                    row[10] == "High",
                    f"DB FORM: energy_level='High'",
                    f"DB FORM: energy_level='{row[10]}'",
                )

            # For voice entries, verify they exist with valid scores
            if row[2] == "VOICE":
                check(
                    row[3] is not None and row[3] > 0,
                    f"DB VOICE: mood_score={row[3]}",
                    f"DB VOICE: mood_score invalid: {row[3]}",
                )
                check(
                    row[4] is not None and row[4] > 0,
                    f"DB VOICE: stress_level={row[4]}",
                    f"DB VOICE: stress_level invalid: {row[4]}",
                )
                check(
                    row[5] is not None and row[5] > 0,
                    f"DB VOICE: burnout_risk={row[5]}",
                    f"DB VOICE: burnout_risk invalid: {row[5]}",
                )
                check(
                    row[6] is not None,
                    f"DB VOICE: sentiment='{row[6]}'",
                    f"DB VOICE: sentiment is None",
                )

        # Check voice_conversations table
        result = conn.execute(
            text(f"""
            SELECT id, user_id, conversation, summary, created_at
            FROM voice_conversations
            WHERE user_id = '{emp_id}'
            ORDER BY created_at DESC
        """)
        )
        vrows = result.fetchall()
        log("DB_VOICE_CONVERSATIONS", f"Total voice conversations: {len(vrows)}")
        for vr in vrows:
            log("DB_VC_ROW", f"  id={str(vr[0])[:8]}... summary={str(vr[3])[:60]}...")

except ImportError:
    log("WARN", "sqlalchemy/psycopg2 not available for direct DB check - skipping")
except Exception as e:
    log("DB_ERROR", f"Direct DB check failed: {type(e).__name__}: {e}")

# ============================================================
# RESULTS SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)

passed = sum(1 for tag, _ in RESULTS if tag == "PASS")
failed = sum(1 for tag, _ in RESULTS if tag == "FAIL")
warned = sum(1 for tag, _ in RESULTS if tag in ("WARN", "SKIP"))
info = sum(
    1
    for tag, _ in RESULTS
    if tag
    in (
        "SETUP",
        "RESPONSE",
        "DB_VERIFY",
        "SUMMARY",
        "CHART",
        "INSIGHT",
        "VOICE_RESPONSE",
        "VOICE_HISTORY",
        "MANAGER_DASH",
        "TABLE_SCHEMA",
        "SCHEMA",
        "DB_ENTRIES",
        "DB_ROW",
        "DB_VC_ROW",
        "DB_VOICE_CONVERSATIONS",
        "IDS",
        "EMP_SUMMARY",
    )
)

print(f"\nTotal: {passed} passed, {failed} failed, {warned} warnings/skips")

if failed > 0:
    print("\n--- FAILED CHECKS ---")
    for tag, msg in RESULTS:
        if tag == "FAIL":
            print(f"  [FAIL] {msg}")
    print(f"\nRESULT: FAIL ({failed} failures)")
else:
    print(f"\nRESULT: PASS (all {passed} checks passed)")

sys.exit(1 if failed > 0 else 0)
