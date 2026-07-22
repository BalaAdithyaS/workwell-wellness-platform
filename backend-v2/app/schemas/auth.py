"""Auth request / response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class UserCreate(BaseModel):
    """Schema for employee/manager registration."""

    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company: str = Field(..., min_length=1, max_length=200)
    team_id: uuid.UUID | None = None
    role: Role = Role.employee


class UserLogin(BaseModel):
    """Schema for login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe representation of a user (no password)."""

    id: uuid.UUID
    name: str
    email: str
    company: str
    team_id: uuid.UUID | None = None
    role: Role
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT wrapper returned after login / signup."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
