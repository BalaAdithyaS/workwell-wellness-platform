from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    team_id: str
    role: str = "employee"


class UserLogin(BaseModel):
    email: EmailStr
    password: str