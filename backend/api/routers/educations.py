from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_db
from api.deps.auth import require_role
from api.schemas.profile import EducationProfileResponse, EducationProfileUpdate, MediaUploadResponse
from api.schemas.user import RoleResponse
from database.schema.base import EducationProfile, User, UserRole

from ._media import save_media_file


router = APIRouter(prefix="/me", tags=["Education"])


def _get_education_profile(db: Session, user_id: UUID) -> EducationProfile | None:
    stmt = sa.select(EducationProfile).where(EducationProfile.user_id == user_id)
    return db.scalar(stmt)


@router.get("/education", response_model=RoleResponse)
async def read_education(user: User = Depends(require_role(UserRole.EDUCATION))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/education/profile", response_model=EducationProfileResponse)
async def get_education_profile(
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationProfile:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/education/profile", response_model=EducationProfileResponse)
async def update_education_profile(
    payload: EducationProfileUpdate,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationProfile:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        profile = EducationProfile(user_id=user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/education/logo", response_model=MediaUploadResponse)
async def upload_education_logo(
    logo: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        profile = EducationProfile(user_id=user.id)
        db.add(profile)

    profile.logo_url = save_media_file(logo, f"education/{user.id}", profile.logo_url)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.logo_url or "")
