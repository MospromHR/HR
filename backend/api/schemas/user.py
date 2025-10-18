from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from database.schema.base import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    is_superuser: bool
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    is_active: bool | None = None


class RoleResponse(BaseModel):
    role: UserRole
