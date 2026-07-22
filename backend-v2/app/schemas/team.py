"""Team request / response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class TeamResponse(BaseModel):
    """A team returned to the client."""

    id: uuid.UUID
    name: str
    company: str
    created_at: datetime

    model_config = {"from_attributes": True}
