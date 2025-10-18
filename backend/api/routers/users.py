from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID, uuid4

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.deps import get_db
from api.deps.auth import get_current_superuser, get_current_user, require_role
from database.schema.base import (
    ApplicantProfile,
    CompanyProfile,
    EducationProfile,
    User,
    UserRole,
)

from ..schemas.profile import (
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    EducationProfileResponse,
    EducationProfileUpdate,
    MediaUploadResponse,
)
from ..schemas.user import RoleResponse, UserResponse


router = APIRouter()
MEDIA_ROOT = Path.cwd() / "media"


def _ensure_media_root() -> None:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)


def _save_media_file(upload: UploadFile, subdir: str, previous_path: str | None = None) -> str:
    _ensure_media_root()
    suffix = Path(upload.filename or "").suffix.lower() or ".bin"
    filename = f"{uuid4().hex}{suffix}"
    relative_path = Path("media") / subdir / filename
    absolute_path = Path.cwd() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    upload.file.seek(0)
    with absolute_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    if previous_path:
        previous = Path(previous_path.lstrip("/"))
        previous_absolute = (Path.cwd() / previous).resolve()
        media_root = MEDIA_ROOT.resolve()
        try:
            is_inside_media = previous_absolute.is_relative_to(media_root)
        except AttributeError:
            is_inside_media = str(previous_absolute).startswith(str(media_root))

        if previous_absolute.is_file() and is_inside_media:
            try:
                previous_absolute.unlink()
            except FileNotFoundError:
                pass

    return "/" + relative_path.as_posix()


def _get_applicant_profile(db: Session, user_id: UUID) -> ApplicantProfile | None:
    stmt = sa.select(ApplicantProfile).where(ApplicantProfile.user_id == user_id)
    return db.scalar(stmt)


def _get_company_profile(db: Session, user_id: UUID) -> CompanyProfile | None:
    stmt = sa.select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    return db.scalar(stmt)


def _get_education_profile(db: Session, user_id: UUID) -> EducationProfile | None:
    stmt = sa.select(EducationProfile).where(EducationProfile.user_id == user_id)
    return db.scalar(stmt)


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


@router.get("/me/applicant/profile", response_model=ApplicantProfileResponse)
async def get_applicant_profile(
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantProfile:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me/applicant/profile", response_model=ApplicantProfileResponse)
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


@router.post("/me/applicant/avatar", response_model=MediaUploadResponse)
async def upload_applicant_avatar(
    avatar: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        profile = ApplicantProfile(user_id=user.id)
        db.add(profile)

    profile.avatar_url = _save_media_file(avatar, f"applicants/{user.id}", profile.avatar_url)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.avatar_url or "")


@router.get("/me/company/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me/company/profile", response_model=CompanyProfileResponse)
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


@router.post("/me/company/logo", response_model=MediaUploadResponse)
async def upload_company_logo(
    logo: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        profile = CompanyProfile(user_id=user.id)
        db.add(profile)

    profile.logo_url = _save_media_file(logo, f"companies/{user.id}", profile.logo_url)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.logo_url or "")


@router.get("/me/education/profile", response_model=EducationProfileResponse)
async def get_education_profile(
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationProfile:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/me/education/profile", response_model=EducationProfileResponse)
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


@router.post("/me/education/logo", response_model=MediaUploadResponse)
async def upload_education_logo(
    logo: UploadFile = File(...),
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> MediaUploadResponse:
    profile = _get_education_profile(db, user.id)
    if profile is None:
        profile = EducationProfile(user_id=user.id)
        db.add(profile)

    profile.logo_url = _save_media_file(logo, f"education/{user.id}", profile.logo_url)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.logo_url or "")


@router.get("/admin/users", response_model=list[UserResponse])
async def list_users(
    _: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
) -> list[User]:
    stmt = sa.select(User).order_by(User.created_at)
    return list(db.scalars(stmt))
