"""Authentication business logic."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse

logger = logging.getLogger(__name__)


def signup(db: Session, payload: UserCreate) -> TokenResponse:
    """Register a new user and return a JWT."""

    existing = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if existing:
        logger.warning("Signup attempt with existing email: %s", payload.email)
        raise ValueError("Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        company=payload.company,
        team_id=payload.team_id,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User created: %s (id=%s)", user.email, user.id)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


def login(db: Session, payload: UserLogin) -> TokenResponse:
    """Authenticate and return a JWT."""

    user = db.execute(
        select(User).where(User.email == payload.email)
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning("Failed login attempt for: %s", payload.email)
        raise ValueError("Invalid email or password")

    logger.info("User logged in: %s", user.email)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
