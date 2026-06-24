from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.db import Base

class ConversationTemplate(Base):

    __tablename__ = "conversation_templates"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    title = Column(String)

    questions = Column(JSON)

    created_by = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )