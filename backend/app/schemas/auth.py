from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str
    role: str
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
