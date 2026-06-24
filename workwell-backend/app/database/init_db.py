from app.models.user import User
from app.models.wellness import WellnessEntry
from app.models.conversation import ConversationTemplate
from app.models.voice_assessment import VoiceAssessment

from app.database.db import engine
from app.database.db import Base

Base.metadata.create_all(bind=engine)

print("Tables created successfully")