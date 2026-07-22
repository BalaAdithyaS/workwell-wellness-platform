"""WellnessEntry ORM model — single source of truth for all analytics."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Source(str, enum.Enum):
    """Where the wellness data came from."""

    FORM = "FORM"
    VOICE = "VOICE"


class WellnessEntry(Base):
    """One wellness record per submission (form or voice)."""

    __tablename__ = "wellness_entries"
    __table_args__ = (Index("ix_wellness_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source: Mapped[Source] = mapped_column(
        Enum(Source, name="source_enum", create_constraint=True),
        nullable=False,
    )
    mood_score: Mapped[int] = mapped_column(Integer, nullable=False)
    stress_level: Mapped[int] = mapped_column(Integer, nullable=False)
    burnout_risk: Mapped[int] = mapped_column(Integer, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<WellnessEntry {self.id} user={self.user_id} source={self.source.value}>"
        )
