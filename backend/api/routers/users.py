import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db
from api.deps.auth import get_current_superuser, get_current_user, require_role
from database.schema.base import User, UserRole

from ..schemas.user import RoleResponse, UserResponse


router = APIRouter()


@router.get("/me", response_model=RoleResponse)
async def read_profile(user: User = Depends(get_current_user)) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/me/company", response_model=RoleResponse)
async def read_company(user: User = Depends(require_role(UserRole.COMPANY))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/me/education", response_model=RoleResponse)
async def read_education(user: User = Depends(require_role(UserRole.EDUCATION))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/me/profile", response_model=RoleResponse)
async def read_applicant(user: User = Depends(require_role(UserRole.APPLICANT))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/admin/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[User]:
    stmt = sa.select(User).order_by(User.created_at)
    return list(db.scalars(stmt))
