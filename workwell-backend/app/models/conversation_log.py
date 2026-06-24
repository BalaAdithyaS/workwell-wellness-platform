from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.db import Base

class ConversationLog(Base):

    __tablename__ = "conversation_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id = Column(String)

    speaker = Column(String)

    message = Column(Text)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )