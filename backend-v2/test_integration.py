"""End-to-end integration test: frontend endpoints vs backend."""

import httpx
import json

BASE = "http://127.0.0.1:8000"
results = []


def test(name, method, url, **kwargs):
    try:
        r = getattr(httpx, method)(url, timeout=30, **kwargs)
        ok = r.status_code < 400
        results.append((name, r.status_code, "PASS" if ok else "FAIL", r.text[:300]))
        return r
    except Exception as e:
        results.append((name, 0, "ERROR", str(e)[:300]))
        return None


# 1. Signup employee
r = test(
    "1. Signup employee",
    "post",
    f"{BASE}/auth/signup",
    json={
        "name": "TestEmployee",
        "email": "e2e_emp@test.com",
        "password": "password123",
        "company": "TestCo",
        "role": "employee",
    },
)
# 2. Signup manager
r = test(
    "2. Signup manager",
    "post",
    f"{BASE}/auth/signup",
    json={
        "name": "TestManager",
        "email": "e2e_mgr@test.com",
        "password": "password123",
        "company": "TestCo",
        "role": "manager",
    },
)

# 3. Login employee
r = test(
    "3. Login employee",
    "post",
    f"{BASE}/auth/login",
    json={"email": "e2e_emp@test.com", "password": "password123"},
)
emp_token = r.json().get("access_token") if r and r.status_code < 400 else None
emp_h = {"Authorization": f"Bearer {emp_token}"} if emp_token else {}

# 4. Login manager
r = test(
    "4. Login manager",
    "post",
    f"{BASE}/auth/login",
    json={"email": "e2e_mgr@test.com", "password": "password123"},
)
mgr_token = r.json().get("access_token") if r and r.status_code < 400 else None
mgr_h = {"Authorization": f"Bearer {mgr_token}"} if mgr_token else {}

# 5. Create wellness (employee)
r = test(
    "5. Create wellness",
    "post",
    f"{BASE}/wellness/create",
    json={
        "mood_score": 7,
        "stress_level": 4,
        "burnout_risk": 3,
        "sentiment": "positive",
        "recommendation": "Good job",
        "notes": "Testing",
    },
    headers=emp_h,
)

# 6. Wellness history (employee)
r = test(
    "6. Wellness history",
    "get",
    f"{BASE}/wellness/history?skip=0&limit=50",
    headers=emp_h,
)
if r and r.status_code == 200:
    print(f"    -> Got {len(r.json())} history entries")

# 7. Analytics summary (employee)
r = test("7. Analytics summary", "get", f"{BASE}/analytics/summary", headers=emp_h)
if r and r.status_code == 200:
    print(f"    -> {r.json()}")

# 8. Analytics chart (employee)
r = test("8. Analytics chart", "get", f"{BASE}/analytics/chart", headers=emp_h)
if r and r.status_code == 200:
    print(f"    -> Got {len(r.json())} chart points")

# 9. Analytics ai-insight (employee)
r = test(
    "9. Analytics ai-insight", "get", f"{BASE}/analytics/ai-insight", headers=emp_h
)
if r and r.status_code == 200:
    print(f"    -> {r.json()}")

# 10. Manager dashboard
r = test("10. Manager dashboard", "get", f"{BASE}/manager/dashboard", headers=mgr_h)
if r and r.status_code == 200:
    d = r.json()
    print(
        f"    -> company={d['company']}, employees={d['total_employees']}, entries={d['total_entries']}"
    )

# 11. Auth me (employee)
r = test("11. Auth me", "get", f"{BASE}/auth/me", headers=emp_h)
if r and r.status_code == 200:
    print(f"    -> {r.json()['name']} ({r.json()['role']})")

# Print summary
print("\n=== INTEGRATION TEST RESULTS ===")
passed = sum(1 for _, _, res, _ in results if res == "PASS")
failed = sum(1 for _, _, res, _ in results if res != "PASS")
for name, status, result, body in results:
    icon = "PASS" if result == "PASS" else ("FAIL" if result == "FAIL" else "ERR ")
    line = f"  [{icon}] {name} -> {status}"
    print(line)
    if result != "PASS":
        print(f"         {body[:200]}")
print(f"\nTotal: {passed} passed, {failed} failed")
