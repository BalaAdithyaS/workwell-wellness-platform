
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database.db import Base

class WellnessEntry(Base):

    __tablename__ = "wellness_entries"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id")
    )

    mood_score = Column(Integer)

    stress_level = Column(Integer)

    notes = Column(Text)
    
    sentiment = Column(String)
    
    burnout_risk = Column(Integer)
    
    recommendation = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

