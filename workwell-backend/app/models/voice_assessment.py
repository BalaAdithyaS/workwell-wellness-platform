from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.db import Base

class VoiceAssessment(Base):

    __tablename__ = "voice_assessments"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(String)

    sentiment = Column(String)

    risk_level = Column(String)

    recommendation = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )