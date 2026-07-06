from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    team_id: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str