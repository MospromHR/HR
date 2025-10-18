from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.deps.auth import get_current_superuser
from api.schemas.user import UserResponse
from database.schema.base import User


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[User]:
    stmt = sa.select(User).order_by(User.created_at)
    return list(db.scalars(stmt))
