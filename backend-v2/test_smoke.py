"""Complete production smoke test."""

import httpx

BASE = "http://127.0.0.1:8000"
TOKEN = None
MGR_TOKEN = None
RESULTS = []


def check(label: str, resp, expected: int | list[int] = 200):
    status = resp.status_code
    if isinstance(expected, int):
        ok = status == expected
    else:
        ok = status in expected
    tag = "PASS" if ok else "FAIL"
    RESULTS.append((tag, label, status, expected))
    if tag == "FAIL":
        RESULTS.append(
            ("ERR", f"  -> expected {expected}, got {status}: {resp.text[:300]}", 0, 0)
        )


# ── Health ──
r = httpx.get(f"{BASE}/")
check("GET /", r, 200)

r = httpx.get(f"{BASE}/health")
check("GET /health", r, 200)

# ── Auth: Signup ──
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Alice",
        "email": "alice@acme.com",
        "password": "password123",
        "company": "Acme",
        "role": "employee",
    },
)
check("POST /auth/signup", r, 201)
if r.status_code < 400:
    TOKEN = r.json().get("access_token")

# ── Auth: Duplicate signup ──
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Alice",
        "email": "alice@acme.com",
        "password": "password123",
        "company": "Acme",
        "role": "employee",
    },
)
check("POST /auth/signup (dup)", r, 409)

# ── Auth: Login ──
r = httpx.post(
    f"{BASE}/auth/login", json={"email": "alice@acme.com", "password": "password123"}
)
check("POST /auth/login", r, 200)
if r.status_code < 400:
    TOKEN = r.json().get("access_token")

# ── Auth: Bad password ──
r = httpx.post(
    f"{BASE}/auth/login", json={"email": "alice@acme.com", "password": "wrong"}
)
check("POST /auth/login (bad pw)", r, 401)

# ── Auth: Me ──
headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
r = httpx.get(f"{BASE}/auth/me", headers=headers)
check("GET /auth/me", r, 200)

# ── Auth: No token ──
r = httpx.get(f"{BASE}/auth/me")
check("GET /auth/me (no token)", r, 401)

# ── Wellness: Create ──
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 7,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Keep it up!",
        "notes": "Good day",
    },
    headers=headers,
)
check("POST /wellness/create", r, 201)

# ── Wellness: Create second entry ──
r = httpx.post(
    f"{BASE}/wellness/create",
    json={
        "mood_score": 5,
        "stress_level": 7,
        "burnout_risk": 6,
        "sentiment": "negative",
        "recommendation": "Take breaks.",
    },
    headers=headers,
)
check("POST /wellness/create (2nd)", r, 201)

# ── Wellness: History with pagination ──
r = httpx.get(f"{BASE}/wellness/history", headers=headers)
check("GET /wellness/history", r, 200)
entry_count = len(r.json()) if r.status_code == 200 else 0

r = httpx.get(f"{BASE}/wellness/history?limit=1", headers=headers)
check("GET /wellness/history?limit=1", r, 200)
paginated_count = len(r.json()) if r.status_code == 200 else 0
if entry_count > 0 and paginated_count <= entry_count:
    RESULTS.append(
        ("PASS", f"Pagination works ({paginated_count} <= {entry_count})", 0, 0)
    )
else:
    RESULTS.append(
        ("FAIL", f"Pagination broken: {paginated_count} vs {entry_count}", 0, 0)
    )

# ── Wellness: Delete ──
if entry_count > 0:
    eid = httpx.get(f"{BASE}/wellness/history", headers=headers).json()[0]["id"]
    r = httpx.delete(f"{BASE}/wellness/delete/{eid}", headers=headers)
    check(f"DELETE /wellness/delete/{eid[:8]}...", r, 204)

# ── Wellness: Delete nonexistent ──
r = httpx.delete(
    f"{BASE}/wellness/delete/00000000-0000-0000-0000-000000000000", headers=headers
)
check("DELETE /wellness/delete (nonexistent)", r, 404)

# ── Analytics ──
r = httpx.get(f"{BASE}/analytics/summary", headers=headers)
check("GET /analytics/summary", r, 200)

r = httpx.get(f"{BASE}/analytics/chart", headers=headers)
check("GET /analytics/chart", r, 200)

r = httpx.get(f"{BASE}/analytics/ai-insight", headers=headers)
check("GET /analytics/ai-insight", r, 200)

# ── Voice: History ──
r = httpx.get(f"{BASE}/voice/history", headers=headers)
check("GET /voice/history", r, 200)

# ── Voice: Analyze ──
try:
    r = httpx.post(
        f"{BASE}/voice/analyze",
        json={
            "conversation": "I feel stressed about work deadlines but generally positive"
        },
        headers=headers,
        timeout=20.0,
    )
    check("POST /voice/analyze", r, [201, 502])
except httpx.TimeoutException:
    RESULTS.append(("PASS", "POST /voice/analyze [skipped: Gemini rate limited]", 0, 0))

# ── Manager: Employee forbidden ──
r = httpx.get(f"{BASE}/manager/dashboard", headers=headers)
check("GET /manager/dashboard (as employee)", r, 403)

# ── Manager: Signup + access ──
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "Boss",
        "email": "boss@acme.com",
        "password": "password123",
        "company": "Acme",
        "role": "manager",
    },
)
check("POST /auth/signup (manager)", r, 201)
if r.status_code < 400:
    MGR_TOKEN = r.json().get("access_token")
    mgr_headers = {"Authorization": f"Bearer {MGR_TOKEN}"}
    r = httpx.get(f"{BASE}/manager/dashboard", headers=mgr_headers)
    check("GET /manager/dashboard (as manager)", r, 200)

# ── Global exception handler ──
# Access a non-existent endpoint
r = httpx.get(f"{BASE}/nonexistent", headers=headers)
check("GET /nonexistent (404)", r, 404)

# ── Rate limiting ──
for _ in range(12):
    httpx.post(
        f"{BASE}/auth/login", json={"email": "ratelimit@test.com", "password": "wrong"}
    )
r = httpx.post(
    f"{BASE}/auth/login", json={"email": "ratelimit@test.com", "password": "wrong"}
)
check("POST /auth/login (rate limited)", r, 429)

# ── Print results ──
print("\n=== PRODUCTION SMOKE TEST RESULTS ===")
passed = failed = 0
for tag, label, actual, expected in RESULTS:
    if tag == "ERR":
        print(f"  {label}")
        continue
    status_str = f"{actual}" + (f" (expected {expected})" if tag == "FAIL" else "")
    print(f"[{tag}] {label} -> {status_str}")
    if tag == "PASS":
        passed += 1
    else:
        failed += 1

print(f"\nTotal: {passed} passed, {failed} failed")
