"""Migration: add sleep_hours and energy_level to wellness_entries."""

from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:1234@localhost:5432/workwell")
with engine.connect() as conn:
    try:
        conn.execute(
            text("ALTER TABLE wellness_entries ADD COLUMN sleep_hours DOUBLE PRECISION")
        )
        print("Added sleep_hours column")
    except Exception as e:
        print(f"sleep_hours note: {e}")

    try:
        conn.execute(
            text("ALTER TABLE wellness_entries ADD COLUMN energy_level VARCHAR(50)")
        )
        print("Added energy_level column")
    except Exception as e:
        print(f"energy_level note: {e}")

    conn.commit()
    print("Migration complete")
