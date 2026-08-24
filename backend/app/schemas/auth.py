from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)
    role: UserRole = UserRole.CUSTOMER


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: UserRole
    exp: int
    type: str


from datetime import datetime
from uuid import UUID


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str
