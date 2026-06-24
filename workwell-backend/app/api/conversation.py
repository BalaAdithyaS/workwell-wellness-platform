from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.conversation_log import ConversationLog

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/save")
def save_message(
    user_id: str,
    speaker: str,
    message: str,
    db: Session = Depends(get_db)
):

    log = ConversationLog(
        user_id=user_id,
        speaker=speaker,
        message=message
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "message": "saved",
        "id": str(log.id)
    }


@router.get("/history/{user_id}")
def get_history(
    user_id: str,
    db: Session = Depends(get_db)
):

    data = (
        db.query(ConversationLog)
        .filter(
            ConversationLog.user_id == user_id
        )
        .all()
    )

    return [
        {
            "id": str(row.id),
            "user_id": row.user_id,
            "speaker": row.speaker,
            "message": row.message,
            "created_at": row.created_at
        }
        for row in data
    ]