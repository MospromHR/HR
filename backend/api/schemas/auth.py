from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from database.schema.base import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)
