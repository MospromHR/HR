from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session
from typing import Literal
from uuid import UUID

from api.deps import get_config, get_db, get_stats_cache
from api.deps.auth import require_role
from api.schemas.analytics import EducationStatsResponse
from api.schemas.profile import EducationProfileResponse, EducationProfileUpdate, MediaUploadResponse
from api.schemas.user import RoleResponse
from api.services import SimpleTTLCache
from api.services.analytics import get_education_stats
from api.services.export import build_education_stats_report, build_report_filename
from config import Config
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


@router.get("/education/stats", response_model=EducationStatsResponse)
async def get_education_stats_endpoint(
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
    cache: SimpleTTLCache[EducationStatsResponse] = Depends(get_stats_cache),
) -> EducationStatsResponse:
    cache_key = f"education-stats:{user.id}"
    return cache.get_or_set(cache_key, lambda: get_education_stats(db, user.id))


@router.get("/education/stats/export")
async def export_education_stats(
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
    cache: SimpleTTLCache[EducationStatsResponse] = Depends(get_stats_cache),
    export_format: Literal["xlsx"] = Query(
        "xlsx", description="Формат выгрузки отчета", alias="format"
    ),
) -> Response:
    if export_format != "xlsx":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported format")

    cache_key = f"education-stats:{user.id}"
    stats = cache.get_or_set(cache_key, lambda: get_education_stats(db, user.id))

    report_content = build_education_stats_report(stats)
    filename = build_report_filename("education-stats")
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(
        content=report_content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


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
    cfg: Config = Depends(get_config),
) -> MediaUploadResponse:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        profile = EducationProfile(user_id=user.id)
        db.add(profile)

    profile.logo_url = save_media_file(
        logo,
        f"education/{user.id}",
        profile.logo_url,
        media_root=cfg.storage.media_root,
        public_prefix=cfg.storage.public_path_prefix,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.logo_url or "")
