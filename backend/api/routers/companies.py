from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_config, get_db
from api.deps.auth import require_role
from api.schemas.profile import CompanyProfileResponse, CompanyProfileUpdate, MediaUploadResponse
from api.schemas.user import RoleResponse
from config import Config
from database.schema.base import CompanyProfile, User, UserRole

from ._media import save_media_file


router = APIRouter(prefix="/me", tags=["Companies"])


def _get_company_profile(db: Session, user_id: UUID) -> CompanyProfile | None:
    stmt = sa.select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    return db.scalar(stmt)


@router.get("/company", response_model=RoleResponse)
async def read_company(user: User = Depends(require_role(UserRole.COMPANY))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/company/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/company/profile", response_model=CompanyProfileResponse)
async def update_company_profile(
    payload: CompanyProfileUpdate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        profile = CompanyProfile(user_id=user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/company/logo", response_model=MediaUploadResponse)
async def upload_company_logo(
    logo: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
    cfg: Config = Depends(get_config),
) -> MediaUploadResponse:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        profile = CompanyProfile(user_id=user.id)
        db.add(profile)

    profile.logo_url = save_media_file(
        logo,
        f"companies/{user.id}",
        profile.logo_url,
        media_root=cfg.storage.media_root,
        public_prefix=cfg.storage.public_path_prefix,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.logo_url or "")
