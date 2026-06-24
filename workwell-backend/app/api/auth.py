import token

from app.auth.auth_bearer import verify_token
from fastapi import HTTPException
from sqlalchemy import select

from app.schemas.user_schema import UserLogin
from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.auth.hashing import hash_password

router = APIRouter()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):

    hashed_pw = hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_pw
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "user_id": str(new_user.id)
    }
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

    token = create_access_token(
        data={
            "sub": db_user.email
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role,
        "user_id": str(db_user.id),
        "name": db_user.name
    }
@router.get("/me")
def get_current_user(payload=Depends(verify_token)):

    return {
        "message": "Protected route accessed",
        "user": payload
    }