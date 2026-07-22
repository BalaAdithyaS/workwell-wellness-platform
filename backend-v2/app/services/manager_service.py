"""Manager dashboard business logic."""

import logging
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Role, User
from app.models.wellness import WellnessEntry
from app.schemas.analytics import EmployeeSummary, ManagerDashboard
from app.services.analytics_service import _burnout_level

logger = logging.getLogger(__name__)


def get_manager_dashboard(db: Session, manager: User) -> ManagerDashboard:
    """Build organization-wide wellness dashboard for a manager."""
    employees = (
        db.execute(
            select(User)
            .where(User.company == manager.company)
            .where(User.role == Role.employee)
        )
        .scalars()
        .all()
    )

    employee_ids = [e.id for e in employees]

    if not employee_ids:
        return ManagerDashboard(
            company=manager.company,
            total_employees=0,
            total_entries=0,
            avg_mood=0.0,
            avg_stress=0.0,
            avg_burnout=0.0,
            burnout_high_count=0,
            burnout_medium_count=0,
            burnout_low_count=0,
            top_recommendations=[],
            employee_summaries=[],
        )

    entries = (
        db.execute(select(WellnessEntry).where(WellnessEntry.user_id.in_(employee_ids)))
        .scalars()
        .all()
    )

    total_entries = len(entries)
    if total_entries == 0:
        avg_mood = avg_stress = avg_burnout = 0.0
    else:
        avg_mood = round(sum(e.mood_score for e in entries) / total_entries, 2)
        avg_stress = round(sum(e.stress_level for e in entries) / total_entries, 2)
        avg_burnout = round(sum(e.burnout_risk for e in entries) / total_entries, 2)

    burnout_counts = Counter(_burnout_level(e.burnout_risk) for e in entries)

    seen_recs: list[str] = []
    for e in entries:
        if e.recommendation not in seen_recs:
            seen_recs.append(e.recommendation)
    top_recs = seen_recs[:5]

    emp_map: dict[uuid.UUID, User] = {e.id: e for e in employees}
    entry_groups: dict[uuid.UUID, list[WellnessEntry]] = {}
    for e in entries:
        entry_groups.setdefault(e.user_id, []).append(e)

    emp_summaries: list[EmployeeSummary] = []
    for eid, emp_entries in entry_groups.items():
        emp_entries_sorted = sorted(
            emp_entries, key=lambda x: x.created_at, reverse=True
        )
        n = len(emp_entries_sorted)
        emp_summaries.append(
            EmployeeSummary(
                user_id=eid,
                name=emp_map[eid].name,
                entries=n,
                avg_mood=round(sum(e.mood_score for e in emp_entries_sorted) / n, 2),
                avg_stress=round(
                    sum(e.stress_level for e in emp_entries_sorted) / n, 2
                ),
                avg_burnout=round(
                    sum(e.burnout_risk for e in emp_entries_sorted) / n, 2
                ),
                latest_sentiment=emp_entries_sorted[0].sentiment,
                burnout_risk_level=_burnout_level(
                    int(sum(e.burnout_risk for e in emp_entries_sorted) / n)
                ),
            )
        )

    return ManagerDashboard(
        company=manager.company,
        total_employees=len(employees),
        total_entries=total_entries,
        avg_mood=avg_mood,
        avg_stress=avg_stress,
        avg_burnout=avg_burnout,
        burnout_high_count=burnout_counts.get("high", 0),
        burnout_medium_count=burnout_counts.get("medium", 0),
        burnout_low_count=burnout_counts.get("low", 0),
        top_recommendations=top_recs,
        employee_summaries=emp_summaries,
    )
