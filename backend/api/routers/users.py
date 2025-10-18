from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps.auth import get_current_user
from api.schemas.user import RoleResponse
from database.schema.base import User


router = APIRouter()


@router.get("/me", response_model=RoleResponse)
async def read_profile(user: User = Depends(get_current_user)) -> RoleResponse:
    return RoleResponse(role=user.role)
