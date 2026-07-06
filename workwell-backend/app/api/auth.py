from app.auth.auth_bearer import verify_token
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token


router = APIRouter()


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Signup
@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):

    try:
        # Check if email already exists
        existing_user = db.execute(
            select(User).where(User.email == user.email)
        ).scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_pw = hash_password(user.password)

        new_user = User(
            name=user.name,
            email=user.email,
            password_hash=hashed_pw,
            team_id=user.team_id
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User created successfully",
            "user_id": str(new_user.id),
            "team_id": new_user.team_id
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()

        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# Login
@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email"
        )

    if not verify_password(
        user.password,
        db_user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )

    # Fixed manager account
    if db_user.email == "manager@workwell.com":
        role = "manager"

        # Assign the manager to TEAM-001
        if db_user.team_id != "TEAM-001":
            db_user.team_id = "TEAM-001"
            db.commit()
            db.refresh(db_user)

    else:
        role = "employee"

    token = create_access_token(
        data={
            "sub": db_user.email
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "user_id": str(db_user.id),
        "name": db_user.name,
        "team_id": db_user.team_id
    }


# Protected route
@router.get("/me")
def get_current_user(payload=Depends(verify_token)):

    return {
        "message": "Protected route accessed",
        "user": payload
    }