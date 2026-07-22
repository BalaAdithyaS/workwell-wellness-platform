"""Migration: create teams table, add team_id FK to users, seed teams."""

from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")
with engine.connect() as conn:
    conn.execute(
        text("""
        CREATE TABLE IF NOT EXISTS teams (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            company VARCHAR(200) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)
    )

    teams = [
        ("Engineering", "WorkWell"),
        ("Marketing", "WorkWell"),
        ("Design", "WorkWell"),
        ("HR", "WorkWell"),
        ("Sales", "WorkWell"),
    ]
    for name, company in teams:
        conn.execute(
            text(
                "INSERT INTO teams (name, company) VALUES (:name, :company) ON CONFLICT DO NOTHING"
            ),
            {"name": name, "company": company},
        )

    try:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN team_id UUID REFERENCES teams(id) ON DELETE SET NULL"
            )
        )
        print("Added team_id column to users")
    except Exception as e:
        print(f"team_id column note: {e}")

    conn.commit()
    print("Migration complete")
