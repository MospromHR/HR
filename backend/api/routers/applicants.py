from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_db
from api.deps.auth import require_role
from api.schemas.profile import (
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
    MediaUploadResponse,
)
from api.schemas.user import RoleResponse
from database.schema.base import ApplicantProfile, User, UserRole

from ._media import save_media_file


router = APIRouter(prefix="/me", tags=["Applicants"])


def _get_applicant_profile(db: Session, user_id: UUID) -> ApplicantProfile | None:
    stmt = sa.select(ApplicantProfile).where(ApplicantProfile.user_id == user_id)
    return db.scalar(stmt)


@router.get("/profile", response_model=RoleResponse)
async def read_applicant(user: User = Depends(require_role(UserRole.APPLICANT))) -> RoleResponse:
    return RoleResponse(role=user.role)


@router.get("/applicant/profile", response_model=ApplicantProfileResponse)
async def get_applicant_profile(
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantProfile:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/applicant/profile", response_model=ApplicantProfileResponse)
async def update_applicant_profile(
    payload: ApplicantProfileUpdate,
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantProfile:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        profile = ApplicantProfile(user_id=user.id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/applicant/avatar", response_model=MediaUploadResponse)
async def upload_applicant_avatar(
    avatar: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        profile = ApplicantProfile(user_id=user.id)
        db.add(profile)

    profile.avatar_url = save_media_file(avatar, f"applicants/{user.id}", profile.avatar_url)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.avatar_url or "")
