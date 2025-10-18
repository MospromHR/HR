from __future__ import annotations

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_config, get_db
from api.deps.auth import require_role
from api.schemas.profile import CompanyProfileResponse, CompanyProfileUpdate, MediaUploadResponse
from api.schemas.vacancy import VacancyCreate, VacancyListResponse, VacancyResponse
from api.schemas.user import RoleResponse
from config import Config
from database.schema.base import CompanyProfile, CompanyVacancy, User, UserRole, VacancyStatus

from ._media import save_media_file


router = APIRouter(prefix="/me", tags=["Companies"])


def _get_company_profile(db: Session, user_id: UUID) -> CompanyProfile | None:
    stmt = sa.select(CompanyProfile).where(CompanyProfile.user_id == user_id)
    return db.scalar(stmt)


def _get_company_vacancy(db: Session, user_id: UUID, vacancy_id: UUID) -> CompanyVacancy:
    stmt = (
        sa.select(CompanyVacancy)
        .where(CompanyVacancy.user_id == user_id, CompanyVacancy.id == vacancy_id)
        .limit(1)
    )
    vacancy = db.scalar(stmt)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


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


@router.post(
    "/company/vacancies",
    response_model=VacancyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_vacancy(
    payload: VacancyCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = CompanyVacancy(user_id=user.id, status=VacancyStatus.DRAFT, **payload.model_dump(by_alias=False))
    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)
    return vacancy


@router.get("/company/vacancies", response_model=VacancyListResponse)
async def list_company_vacancies(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> VacancyListResponse:
    total_stmt = sa.select(sa.func.count()).where(CompanyVacancy.user_id == user.id)
    total = db.scalar(total_stmt) or 0

    stmt = (
        sa.select(CompanyVacancy)
        .where(CompanyVacancy.user_id == user.id)
        .order_by(CompanyVacancy.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())
    return VacancyListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/company/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    return _get_company_vacancy(db, user.id, vacancy_id)


def _change_vacancy_status(
    db: Session,
    vacancy: CompanyVacancy,
    new_status: VacancyStatus,
) -> CompanyVacancy:
    vacancy.status = new_status
    db.add(vacancy)
    db.commit()
    db.refresh(vacancy)
    return vacancy


@router.post("/company/vacancies/{vacancy_id}/publish", response_model=VacancyResponse)
async def publish_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft vacancies can be published")
    return _change_vacancy_status(db, vacancy, VacancyStatus.PUBLISHED)


@router.post("/company/vacancies/{vacancy_id}/hide", response_model=VacancyResponse)
async def hide_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only published vacancies can be hidden")
    return _change_vacancy_status(db, vacancy, VacancyStatus.DRAFT)


@router.post("/company/vacancies/{vacancy_id}/close", response_model=VacancyResponse)
async def close_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status == VacancyStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vacancy is already closed")
    return _change_vacancy_status(db, vacancy, VacancyStatus.CLOSED)


@router.post("/company/vacancies/{vacancy_id}/open", response_model=VacancyResponse)
async def open_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only closed vacancies can be opened")
    return _change_vacancy_status(db, vacancy, VacancyStatus.PUBLISHED)


@router.delete(
    "/company/vacancies/{vacancy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> Response:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    db.delete(vacancy)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
