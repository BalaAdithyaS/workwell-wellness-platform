from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database.db import Base

class User(Base):

    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(String)

    email = Column(
        String,
        unique=True
    )

    password_hash = Column(String)

    team_id = Column(
    String,
    nullable=False
)

role = Column(
    String,
    nullable=False,
    default="employee"
)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )