from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_db, get_stats_cache
from api.deps.auth import get_current_superuser
from api.schemas.analytics import AdminStatsResponse
from api.schemas.user import UserResponse, UserUpdateRequest
from api.services import SimpleTTLCache
from api.services.analytics import get_admin_stats
from database.schema.base import User, UserRole


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats_endpoint(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
    cache: SimpleTTLCache[AdminStatsResponse] = Depends(get_stats_cache),
) -> AdminStatsResponse:
    return cache.get_or_set("admin-stats", lambda: get_admin_stats(db))


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
    role: UserRole | None = Query(None, description="Filter users by role"),
    is_active: bool | None = Query(None, description="Filter users by active status"),
    created_from: datetime | None = Query(
        None, description="Return users created on or after this datetime"
    ),
    created_to: datetime | None = Query(
        None, description="Return users created on or before this datetime"
    ),
    search: str | None = Query(None, description="Case-insensitive search by email"),
    sort_by: Literal["created_at", "email", "role", "is_active"] = Query("created_at"),
    sort_direction: Literal["asc", "desc"] = Query("asc"),
) -> list[User]:
    stmt = sa.select(User)

    filters: list[sa.ColumnElement[bool]] = []
    if role is not None:
        filters.append(User.role == role)
    if is_active is not None:
        filters.append(User.is_active == is_active)
    if created_from is not None:
        filters.append(User.created_at >= created_from)
    if created_to is not None:
        filters.append(User.created_at <= created_to)
    if search:
        filters.append(User.email.ilike(f"%{search}%"))

    if filters:
        stmt = stmt.where(sa.and_(*filters))

    sort_columns = {
        "created_at": User.created_at,
        "email": User.email,
        "role": User.role,
        "is_active": User.is_active,
    }
    sort_column = sort_columns[sort_by]
    order_clause = sort_column.asc() if sort_direction == "asc" else sort_column.desc()

    stmt = stmt.order_by(order_clause, User.id)

    return list(db.scalars(stmt))


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No updates were provided"
        )

    user.is_active = payload.is_active

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
