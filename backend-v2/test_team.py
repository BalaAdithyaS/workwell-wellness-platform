import httpx

BASE = "http://127.0.0.1:8000"

# Get teams
teams = httpx.get(f"{BASE}/teams").json()
team_id = teams[0]["id"]
print(f"Using team: {teams[0]['name']} ({team_id})")

# Signup with team_id
r = httpx.post(
    f"{BASE}/auth/signup",
    json={
        "name": "TeamTest2",
        "email": "teamtest2@test.com",
        "password": "password123",
        "company": "WorkWell",
        "team_id": team_id,
        "role": "employee",
    },
    timeout=10,
)
print(f"Signup: {r.status_code}")
if r.status_code < 400:
    data = r.json()
    print(f"  user.team_id = {data['user']['team_id']}")
    print(f"  user.company = {data['user']['company']}")
    print(f"  user.role = {data['user']['role']}")
else:
    print(f"  Error: {r.text}")
