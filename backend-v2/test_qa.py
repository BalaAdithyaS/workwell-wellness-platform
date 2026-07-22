"""QA Attack Suite — attempts to break every endpoint."""

import httpx
import json
import time

BASE = "http://127.0.0.1:8000"
RESULTS = []
TOKEN = None
MGR_TOKEN = None


def check(label: str, resp, expected: int | list[int], should_crash: bool = False):
    """Check response. If should_crash=True, 500 is a FAIL (server crashed)."""
    status = resp.status_code
    if isinstance(expected, int):
        ok = status == expected
    else:
        ok = status in expected

    # A 500 on invalid input = server crash = always FAIL
    if not should_crash and status == 500 and expected != 500:
        tag = "CRASH"
        RESULTS.append((tag, label, status, "should NOT be 500"))
        return

    tag = "PASS" if ok else "FAIL"
    RESULTS.append((tag, label, status, expected))
    if tag == "FAIL":
        body = resp.text[:300]
        # Check if response is JSON (good) or HTML/text (bad)
        try:
            resp.json()
        except Exception:
            if status >= 400:
                RESULTS.append(("WARN", f"  Non-JSON error body: {body[:100]}", 0, 0))


def safe(label: str, resp):
    """Just check it didn't crash (no 500)."""
    status = resp.status_code
    if status == 500:
        RESULTS.append(("CRASH", label, 500, "must not crash"))
    else:
        RESULTS.append(("PASS", label, status, "no crash"))


# ============================================================
# 1. AUTH ENDPOINTS
# ============================================================
print("\n--- Testing AUTH endpoints ---")

# 1.1 Valid signup (prerequisite)
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Alice",
        "email": "alice@test.com",
        "password": "password123",
        "company": "TestCo",
        "role": "employee",
    },
    timeout=10,
)
if r.status_code == 409:
    r = httpx.post(
        f"{BASE}/auth/login",
        json={"email": "alice@test.com", "password": "password123"},
        timeout=10,
    )
check("signup/login: employee", r, 200)
if r.status_code < 400:
    TOKEN = r.json().get("access_token")

r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Boss",
        "email": "boss@test.com",
        "password": "password123",
        "company": "TestCo",
        "role": "manager",
    },
    timeout=10,
)
if r.status_code == 409:
    r = httpx.post(
        f"{BASE}/auth/login",
        json={"email": "boss@test.com", "password": "password123"},
        timeout=10,
    )
check("signup/login: manager", r, 200)
if r.status_code < 400:
    MGR_TOKEN = r.json().get("access_token")

headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

# 1.2 Duplicate email
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Alice2",
        "email": "alice@test.com",
        "password": "password123",
        "company": "TestCo",
        "role": "employee",
    },
    timeout=10,
)
check("signup: duplicate email", r, 409)

# 1.3 Missing fields
for field in ["name", "email", "password", "company"]:
    payload = {
        "name": "X",
        "email": "x@x.com",
        "password": "password123",
        "company": "X",
    }
    payload.pop(field)
    r = httpx.post(f"{BASE}/auth/signup", json=payload, timeout=10)
    safe(f"signup: missing '{field}'", r)

# 1.4 Empty strings
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "",
        "email": "valid@test.com",
        "password": "password123",
        "company": "X",
    },
    timeout=10,
)
safe("signup: empty name", r)

r = httpx.post(
    f"{BASE}/auth/signup",
    json={"name": "X", "email": "", "password": "password123", "company": "X"},
    timeout=10,
)
safe("signup: empty email", r)

r = httpx.post(
    f"{BASE}/auth/signup",
    json={"name": "X", "email": "valid@test.com", "password": "", "company": "X"},
    timeout=10,
)
safe("signup: empty password", r)

# 1.5 Null values
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": None,
        "email": "valid@test.com",
        "password": "password123",
        "company": "X",
    },
    timeout=10,
)
safe("signup: null name", r)

r = httpx.post(
    f"{BASE}/auth/signup",
    json={"name": "X", "email": None, "password": "password123", "company": "X"},
    timeout=10,
)
safe("signup: null email", r)

# 1.6 Invalid email formats
for bad_email in [
    "notanemail",
    "@domain.com",
    "user@",
    "user@.com",
    "user@domain",
    "user domain@test.com",
    "<script>alert(1)</script>@test.com",
]:
    r = httpx.post(
        f"{BASE}/auth/signup",
        json={
            "name": "X",
            "email": bad_email,
            "password": "password123",
            "company": "X",
        },
        timeout=10,
    )
    safe(f"signup: bad email '{bad_email[:20]}'", r)

# 1.7 Password too short
r = httpx.post(
    f"{BASE}/auth/signup",
    json={"name": "X", "email": "short@test.com", "password": "123", "company": "X"},
    timeout=10,
)
safe("signup: password too short", r)

# 1.8 SQL injection in fields
for sqli in [
    "'; DROP TABLE users; --",
    "1' OR '1'='1",
    "admin'--",
    "1; SELECT * FROM users",
]:
    r = httpx.post(
        f"{BASE}/auth/signup",
        json={
            "name": sqli,
            "email": f"sqli{hash(sqli) % 10000}@test.com",
            "password": "password123",
            "company": "X",
        },
        timeout=10,
    )
    safe(f"signup: SQLi name '{sqli[:25]}'", r)

# 1.9 XSS in fields
for xss in [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
]:
    r = httpx.post(
        f"{BASE}/auth/signup",
        json={
            "name": xss,
            "email": f"xss{hash(xss) % 10000}@test.com",
            "password": "password123",
            "company": "X",
        },
        timeout=10,
    )
    safe(f"signup: XSS name '{xss[:25]}'", r)

# 1.10 Malformed JSON
r = httpx.post(
    f"{BASE}/auth/signup",
    content="not json at all",
    headers={"Content-Type": "application/json"},
    timeout=10,
)
safe("signup: malformed JSON", r)

r = httpx.post(
    f"{BASE}/auth/signup",
    content='{"name": "X", "email": "incomplete"',
    headers={"Content-Type": "application/json"},
    timeout=10,
)
safe("signup: truncated JSON", r)

# 1.11 Empty body
r = httpx.post(
    f"{BASE}/auth/signup",
    content="",
    headers={"Content-Type": "application/json"},
    timeout=10,
)
safe("signup: empty body", r)

# 1.12 Wrong Content-Type
r = httpx.post(
    f"{BASE}/auth/signup",
    content="name=X&email=test@test.com",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10,
)
safe("signup: wrong content type", r)

# 1.13 Invalid role
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "X",
        "email": "admin@test.com",
        "password": "password123",
        "company": "X",
        "role": "superadmin",
    },
    timeout=10,
)
safe("signup: invalid role", r)

# 1.14 Login — missing fields
r = httpx.post(f"{BASE}/auth/login", json={"email": "alice@test.com"}, timeout=10)
safe("login: missing password", r)

r = httpx.post(f"{BASE}/auth/login", json={"password": "password123"}, timeout=10)
safe("login: missing email", r)

# 1.15 Login — invalid email
r = httpx.post(
    f"{BASE}/auth/login",
    json={"email": "nonexistent@test.com", "password": "password123"},
    timeout=10,
)
check("login: nonexistent user", r, 401)

# 1.16 Login — SQL injection
r = httpx.post(
    f"{BASE}/auth/login",
    json={"email": "admin'--@test.com", "password": "anything"},
    timeout=10,
)
safe("login: SQLi email", r)

# 1.17 Login — malformed JSON
r = httpx.post(
    f"{BASE}/auth/login",
    content="!!!",
    headers={"Content-Type": "application/json"},
    timeout=10,
)
safe("login: malformed JSON", r)

# 1.18 /me — no token
r = httpx.get(f"{BASE}/auth/me", timeout=10)
check("me: no token", r, 401)

# 1.19 /me — invalid token
r = httpx.get(
    f"{BASE}/auth/me", headers={"Authorization": "Bearer invalidtoken"}, timeout=10
)
check("me: invalid token", r, 401)

# 1.20 /me — expired token (construct one)
from jose import jwt

expired_token = jwt.encode(
    {"sub": "00000000-0000-0000-0000-000000000000", "exp": 0},
    "supersecretkey",
    algorithm="HS256",
)
r = httpx.get(
    f"{BASE}/auth/me", headers={"Authorization": f"Bearer {expired_token}"}, timeout=10
)
check("me: expired token", r, 401)

# 1.21 /me — token with invalid UUID
bad_uuid_token = jwt.encode(
    {"sub": "not-a-uuid", "exp": 99999999999}, "supersecretkey", algorithm="HS256"
)
r = httpx.get(
    f"{BASE}/auth/me", headers={"Authorization": f"Bearer {bad_uuid_token}"}, timeout=10
)
check("me: bad UUID in token", r, 401)

# 1.22 /me — token with non-existent user
ghost_token = jwt.encode(
    {"sub": "00000000-0000-0000-0000-000000000000", "exp": 99999999999},
    "supersecretkey",
    algorithm="HS256",
)
r = httpx.get(
    f"{BASE}/auth/me", headers={"Authorization": f"Bearer {ghost_token}"}, timeout=10
)
check("me: non-existent user", r, 401)

# 1.23 /me — wrong signing key
wrong_key_token = jwt.encode(
    {"sub": "00000000-0000-0000-0000-000000000000", "exp": 99999999999},
    "wrong-secret-key",
    algorithm="HS256",
)
r = httpx.get(
    f"{BASE}/auth/me",
    headers={"Authorization": f"Bearer {wrong_key_token}"},
    timeout=10,
)
check("me: wrong signing key", r, 401)

# 1.24 /me — Bearer prefix without token
try:
    r = httpx.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer "}, timeout=10)
    safe("me: empty bearer", r)
except Exception as e:
    RESULTS.append(
        ("WARN", f"me: empty bearer -> client-side: {type(e).__name__}", 0, 0)
    )

# 1.25 /me — no Bearer prefix
try:
    r = httpx.get(
        f"{BASE}/auth/me", headers={"Authorization": "Basic abc123"}, timeout=10
    )
    safe("me: wrong auth scheme", r)
except Exception as e:
    RESULTS.append(
        ("WARN", f"me: wrong auth scheme -> client-side: {type(e).__name__}", 0, 0)
    )


# ============================================================
# 2. WELLNESS ENDPOINTS
# ============================================================
print("\n--- Testing WELLNESS endpoints ---")

# 2.1 Valid create
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 7,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good",
        "notes": "OK",
    },
    headers=headers,
    timeout=10,
)
check("wellness create: valid", r, 201)

# 2.2 Missing fields
for field in [
    "mood_score",
    "stress_level",
    "burnout_risk",
    "sentiment",
    "recommendation",
]:
    payload = {
        "mood_score": 7,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good",
    }
    payload.pop(field)
    r = httpx.post(f"{BASE}/wellness/create", json=payload, headers=headers, timeout=10)
    safe(f"wellness create: missing '{field}'", r)

# 2.3 Out of range scores
for field in ["mood_score", "stress_level", "burnout_risk"]:
    for bad_val in [0, -1, 11, 100, 999]:
        r = httpx.post(
            f"{BASE}/wellness/create",
            json={
                "mood_score": 5,
                "stress_level": 5,
                "burnout_risk": 5,
                "sentiment": "neutral",
                "recommendation": "OK",
            }
            | {field: bad_val},
            headers=headers,
            timeout=10,
        )
        safe(f"wellness: {field}={bad_val}", r)

# 2.4 Float scores
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 7.5,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: float mood_score", r)

# 2.5 String scores
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": "high",
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: string mood_score", r)

# 2.6 Null scores
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": None,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: null mood_score", r)

# 2.7 Empty sentiment
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 5,
        "stress_level": 5,
        "burnout_risk": 5,
        "sentiment": "",
        "recommendation": "Good",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: empty sentiment", r)

# 2.8 SQL injection in sentiment
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 5,
        "stress_level": 5,
        "burnout_risk": 5,
        "sentiment": "'; DROP TABLE wellness_entries; --",
        "recommendation": "Good",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: SQLi sentiment", r)

# 2.9 XSS in recommendation
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 5,
        "stress_level": 5,
        "burnout_risk": 5,
        "sentiment": "positive",
        "recommendation": "<script>alert(1)</script>",
    },
    headers=headers,
    timeout=10,
)
safe("wellness: XSS recommendation", r)

# 2.10 No auth
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 5,
        "stress_level": 5,
        "burnout_risk": 5,
        "sentiment": "positive",
        "recommendation": "Good",
    },
    timeout=10,
)
check("wellness create: no auth", r, 401)

# 2.11 History — no auth
r = httpx.get(f"{BASE}/wellness/history", timeout=10)
check("wellness history: no auth", r, 401)

# 2.12 History — negative skip
r = httpx.get(f"{BASE}/wellness/history?skip=-1", headers=headers, timeout=10)
safe("wellness history: skip=-1", r)

# 2.13 History — zero limit
r = httpx.get(f"{BASE}/wellness/history?limit=0", headers=headers, timeout=10)
safe("wellness history: limit=0", r)

# 2.14 History — huge limit
r = httpx.get(f"{BASE}/wellness/history?limit=999999", headers=headers, timeout=10)
safe("wellness history: limit=999999", r)

# 2.15 History — string limit
r = httpx.get(f"{BASE}/wellness/history?limit=abc", headers=headers, timeout=10)
safe("wellness history: string limit", r)

# 2.16 Delete — invalid UUID
r = httpx.delete(f"{BASE}/wellness/delete/not-a-uuid", headers=headers, timeout=10)
check("wellness delete: invalid UUID", r, 422)

# 2.17 Delete — no auth
r = httpx.delete(
    f"{BASE}/wellness/delete/00000000-0000-0000-0000-000000000000", timeout=10
)
check("wellness delete: no auth", r, 401)

# 2.18 Malformed JSON body for create
r = httpx.post(
    f"{BASE}/wellness/create",
    content="!!!",
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    timeout=10,
)
safe("wellness create: malformed JSON", r)


# ============================================================
# 3. VOICE ENDPOINTS
# ============================================================
print("\n--- Testing VOICE endpoints ---")

# 3.1 Empty conversation
r = httpx.post(
    f"{BASE}/voice/analyze", json={"conversation": ""}, headers=headers, timeout=10
)
safe("voice analyze: empty conversation", r)

# 3.2 Null conversation
r = httpx.post(
    f"{BASE}/voice/analyze", json={"conversation": None}, headers=headers, timeout=10
)
safe("voice analyze: null conversation", r)

# 3.3 Missing conversation field
r = httpx.post(f"{BASE}/voice/analyze", json={}, headers=headers, timeout=10)
safe("voice analyze: missing field", r)

# 3.4 Very large conversation (over limit)
big = "I am stressed. " * 5000  # ~75k chars
r = httpx.post(
    f"{BASE}/voice/analyze", json={"conversation": big}, headers=headers, timeout=10
)
safe("voice analyze: huge body", r)

# 3.5 SQL injection in conversation
r = httpx.post(
    f"{BASE}/voice/analyze",
    json={"conversation": "'; DROP TABLE voice_conversations; --"},
    headers=headers,
    timeout=10,
)
safe("voice analyze: SQLi", r)

# 3.6 XSS in conversation
r = httpx.post(
    f"{BASE}/voice/analyze",
    json={"conversation": "<script>alert(1)</script>"},
    headers=headers,
    timeout=10,
)
safe("voice analyze: XSS", r)

# 3.7 No auth
r = httpx.post(f"{BASE}/voice/analyze", json={"conversation": "test"}, timeout=10)
check("voice analyze: no auth", r, 401)

# 3.8 History — no auth
r = httpx.get(f"{BASE}/voice/history", timeout=10)
check("voice history: no auth", r, 401)

# 3.9 History — pagination edge cases
r = httpx.get(f"{BASE}/voice/history?skip=-1", headers=headers, timeout=10)
safe("voice history: skip=-1", r)

r = httpx.get(f"{BASE}/voice/history?limit=0", headers=headers, timeout=10)
safe("voice history: limit=0", r)


# ============================================================
# 4. ANALYTICS ENDPOINTS
# ============================================================
print("\n--- Testing ANALYTICS endpoints ---")

for ep in ["/analytics/summary", "/analytics/chart", "/analytics/ai-insight"]:
    # No auth
    r = httpx.get(f"{BASE}{ep}", timeout=10)
    check(f"analytics {ep}: no auth", r, 401)

    # Valid
    r = httpx.get(f"{BASE}{ep}", headers=headers, timeout=10)
    safe(f"analytics {ep}: valid", r)


# ============================================================
# 5. MANAGER ENDPOINTS
# ============================================================
print("\n--- Testing MANAGER endpoints ---")

# 5.1 Employee can't access
r = httpx.get(f"{BASE}/manager/dashboard", headers=headers, timeout=10)
check("manager: employee forbidden", r, 403)

# 5.2 No auth
r = httpx.get(f"{BASE}/manager/dashboard", timeout=10)
check("manager: no auth", r, 401)

# 5.3 Manager can access
mgr_headers = {"Authorization": f"Bearer {MGR_TOKEN}"} if MGR_TOKEN else {}
r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_headers, timeout=10)
check("manager: valid access", r, 200)


# ============================================================
# 6. GENERAL ATTACKS
# ============================================================
print("\n--- Testing GENERAL attacks ---")

# 6.1 Unknown endpoint
r = httpx.get(f"{BASE}/admin/shutdown", timeout=10)
check("general: unknown endpoint", r, 404)

# 6.2 Method not allowed
r = httpx.delete(f"{BASE}/auth/signup", timeout=10)
safe("general: wrong method", r)

# 6.3 Path traversal
r = httpx.get(f"{BASE}/../../../etc/passwd", timeout=10)
safe("general: path traversal", r)

# 6.4 Null bytes in URL
r = httpx.get(f"{BASE}/%00%00%00", timeout=10)
safe("general: null bytes", r)

# 6.5 Giant URL
r = httpx.get(f"{BASE}/?" + "a" * 10000, timeout=10)
safe("general: giant query string", r)

# 6.6 Missing Content-Type header
r = httpx.post(f"{BASE}/auth/signup", content=b'{"name":"X"}', timeout=10)
safe("general: missing content type", r)

# 6.7 OPTIONS preflight
r = httpx.options(
    f"{BASE}/auth/signup",
    headers={"Origin": "http://evil.com", "Access-Control-Request-Method": "POST"},
    timeout=10,
)
check("general: CORS preflight", r, [200, 400, 405])


# ============================================================
# RESULTS
# ============================================================
print("\n=== QA ATTACK SUITE RESULTS ===")
passed = failed = crashed = warned = 0
for tag, label, actual, expected in RESULTS:
    if tag == "CRASH":
        print(f"[!!!CRASH!!!] {label} -> 500 (server error)")
        crashed += 1
    elif tag == "WARN":
        print(f"  WARNING: {label}")
        warned += 1
    elif tag == "FAIL":
        print(f"[FAIL] {label} -> {actual} (expected {expected})")
        failed += 1
    else:
        passed += 1

print(
    f"\nTotal: {passed} passed, {failed} failed, {crashed} crashes, {warned} warnings"
)
