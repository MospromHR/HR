from __future__ import annotations

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from api.deps import get_config, get_db, get_stats_cache
from api.deps.auth import require_role
from api.schemas.analytics import CompanyStatsResponse
from api.schemas.profile import (
    ApplicantProfileResponse,
    CompanyListResponse,
    CompanyProfileResponse,
    CompanyProfileUpdate,
    MediaUploadResponse,
)
from api.schemas.user import RoleResponse
from api.schemas.vacancy import (
    CompanyVacancyApplicationListResponse,
    CompanyVacancyApplicationResponse,
    VacancyCreate,
    VacancyListResponse,
    VacancyResponse,
)
from api.services import SimpleTTLCache
from api.services.analytics import get_company_stats
from config import Config
from database.schema.base import (
    ApplicantProfile,
    CompanyProfile,
    CompanyVacancy,
    User,
    UserRole,
    VacancyApplication,
    VacancyApplicationStatus,
    VacancyStatus,
)

from ._media import save_media_file


companies_router = APIRouter(prefix="/companies", tags=["Companies"])
vacancies_router = APIRouter(prefix="/vacancies", tags=["Vacancies"])
me_router = APIRouter(prefix="/me", tags=["Companies"])


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


@me_router.get("/company", response_model=RoleResponse)
async def read_company(user: User = Depends(require_role(UserRole.COMPANY))) -> RoleResponse:
    return RoleResponse(role=user.role)


@me_router.get("/company/profile", response_model=CompanyProfileResponse)
async def get_company_profile(
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyProfile:
    profile = _get_company_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@me_router.get("/company/stats", response_model=CompanyStatsResponse)
async def get_company_stats_endpoint(
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
    cache: SimpleTTLCache[CompanyStatsResponse] = Depends(get_stats_cache),
) -> CompanyStatsResponse:
    cache_key = f"company-stats:{user.id}"
    return cache.get_or_set(cache_key, lambda: get_company_stats(db, user.id))


@me_router.put("/company/profile", response_model=CompanyProfileResponse)
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


@me_router.post("/company/logo", response_model=MediaUploadResponse)
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


@me_router.post(
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


@me_router.get("/company/vacancies", response_model=VacancyListResponse)
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


@me_router.get("/company/vacancies/{vacancy_id}", response_model=VacancyResponse)
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


def _serialize_company_application(
    application: VacancyApplication,
    vacancy: CompanyVacancy,
    applicant_user: User,
    profile: ApplicantProfile | None,
) -> CompanyVacancyApplicationResponse:
    return CompanyVacancyApplicationResponse(
        id=application.id,
        vacancy_id=application.vacancy_id,
        applicant_id=application.user_id,
        status=application.status,
        created_at=application.created_at,
        updated_at=application.updated_at,
        applicant_email=applicant_user.email,
        applicant_profile=(
            ApplicantProfileResponse.model_validate(profile) if profile else None
        ),
        vacancy=VacancyResponse.model_validate(vacancy),
    )


def _get_vacancy_application_for_company(
    db: Session,
    company_id: UUID,
    vacancy_id: UUID,
    application_id: UUID,
) -> tuple[VacancyApplication, CompanyVacancy, User, ApplicantProfile | None]:
    stmt = (
        sa.select(VacancyApplication, CompanyVacancy, User, ApplicantProfile)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .join(User, User.id == VacancyApplication.user_id)
        .join(
            ApplicantProfile,
            ApplicantProfile.user_id == User.id,
            isouter=True,
        )
        .where(
            CompanyVacancy.user_id == company_id,
            CompanyVacancy.id == vacancy_id,
            VacancyApplication.id == application_id,
        )
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    return row


def _list_company_applications(
    db: Session,
    company_id: UUID,
    limit: int,
    offset: int,
    status_filter: VacancyApplicationStatus | None,
    vacancy_id: UUID | None = None,
) -> CompanyVacancyApplicationListResponse:
    filters: list[sa.ColumnElement[bool]] = [CompanyVacancy.user_id == company_id]
    if vacancy_id is not None:
        filters.append(CompanyVacancy.id == vacancy_id)
    if status_filter is not None:
        filters.append(VacancyApplication.status == status_filter)

    total_stmt = (
        sa.select(sa.func.count())
        .select_from(VacancyApplication)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(*filters)
    )
    total = db.scalar(total_stmt) or 0

    stmt = (
        sa.select(VacancyApplication, CompanyVacancy, User, ApplicantProfile)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .join(User, User.id == VacancyApplication.user_id)
        .join(
            ApplicantProfile,
            ApplicantProfile.user_id == User.id,
            isouter=True,
        )
        .where(*filters)
        .order_by(VacancyApplication.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [
        _serialize_company_application(application, vacancy, applicant_user, profile)
        for application, vacancy, applicant_user, profile in rows
    ]
    return CompanyVacancyApplicationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@me_router.post("/company/vacancies/{vacancy_id}/publish", response_model=VacancyResponse)
async def publish_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft vacancies can be published")
    return _change_vacancy_status(db, vacancy, VacancyStatus.PUBLISHED)


@me_router.post("/company/vacancies/{vacancy_id}/hide", response_model=VacancyResponse)
async def hide_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only published vacancies can be hidden")
    return _change_vacancy_status(db, vacancy, VacancyStatus.DRAFT)


@me_router.post("/company/vacancies/{vacancy_id}/close", response_model=VacancyResponse)
async def close_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status == VacancyStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vacancy is already closed")
    return _change_vacancy_status(db, vacancy, VacancyStatus.CLOSED)


@me_router.post("/company/vacancies/{vacancy_id}/open", response_model=VacancyResponse)
async def open_company_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    vacancy = _get_company_vacancy(db, user.id, vacancy_id)
    if vacancy.status != VacancyStatus.CLOSED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only closed vacancies can be opened")
    return _change_vacancy_status(db, vacancy, VacancyStatus.PUBLISHED)


@me_router.delete(
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


@me_router.get(
    "/company/vacancies/applications",
    response_model=CompanyVacancyApplicationListResponse,
)
async def list_company_applications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: VacancyApplicationStatus | None = Query(
        None, alias="status", description="Filter applications by status"
    ),
    vacancy_id: UUID | None = Query(
        None, description="Filter applications by specific vacancy"
    ),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancyApplicationListResponse:
    return _list_company_applications(
        db,
        user.id,
        limit,
        offset,
        status_filter,
        vacancy_id,
    )


@me_router.get(
    "/company/vacancies/{vacancy_id}/applications",
    response_model=CompanyVacancyApplicationListResponse,
)
async def list_company_vacancy_applications(
    vacancy_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: VacancyApplicationStatus | None = Query(
        None, alias="status", description="Filter applications by status"
    ),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancyApplicationListResponse:
    _get_company_vacancy(db, user.id, vacancy_id)
    return _list_company_applications(
        db,
        user.id,
        limit,
        offset,
        status_filter,
        vacancy_id,
    )


def _ensure_pending_application(application: VacancyApplication) -> None:
    if application.status == VacancyApplicationStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application was cancelled")
    if application.status == VacancyApplicationStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application already rejected")
    if application.status == VacancyApplicationStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application already approved")
    if application.status != VacancyApplicationStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application is not pending")


@me_router.post(
    "/company/vacancies/{vacancy_id}/applications/{application_id}/approve",
    response_model=CompanyVacancyApplicationResponse,
)
async def approve_vacancy_application(
    vacancy_id: UUID,
    application_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancyApplicationResponse:
    application, vacancy, applicant_user, profile = _get_vacancy_application_for_company(
        db, user.id, vacancy_id, application_id
    )
    _ensure_pending_application(application)
    application.status = VacancyApplicationStatus.APPROVED
    db.add(application)
    db.commit()
    db.refresh(application)
    return _serialize_company_application(application, vacancy, applicant_user, profile)


@me_router.post(
    "/company/vacancies/{vacancy_id}/applications/{application_id}/reject",
    response_model=CompanyVacancyApplicationResponse,
)
async def reject_vacancy_application(
    vacancy_id: UUID,
    application_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyVacancyApplicationResponse:
    application, vacancy, applicant_user, profile = _get_vacancy_application_for_company(
        db, user.id, vacancy_id, application_id
    )
    _ensure_pending_application(application)
    application.status = VacancyApplicationStatus.REJECTED
    db.add(application)
    db.commit()
    db.refresh(application)
    return _serialize_company_application(application, vacancy, applicant_user, profile)


def _ensure_company_user(db: Session, company_id: UUID) -> User:
    stmt = (
        sa.select(User)
        .where(User.id == company_id, User.role == UserRole.COMPANY, User.is_active.is_(True))
        .limit(1)
    )
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return user


def _resolve_status_filter(status: str | None) -> VacancyStatus | None:
    if status is None:
        return None
    normalized = status.lower()
    if normalized in {"open", "published"}:
        return VacancyStatus.PUBLISHED
    if normalized == "closed":
        return VacancyStatus.CLOSED
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")


def _build_sort_clause(
    sort_by: str,
    sort_order: str,
    allowed_columns: dict[str, sa.ColumnElement],
) -> sa.ColumnElement:
    column = allowed_columns.get(sort_by)
    if column is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field")

    normalized_order = sort_order.lower()
    if normalized_order not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order")

    return column.asc() if normalized_order == "asc" else column.desc()


def _vacancy_filters(
    company_id: UUID | None,
    status: VacancyStatus | None,
    posted_from: datetime | None,
    posted_to: datetime | None,
    search: str | None = None,
) -> list[sa.ColumnElement[bool]]:
    conditions: list[sa.ColumnElement[bool]] = [CompanyVacancy.status != VacancyStatus.DRAFT]

    if company_id is not None:
        conditions.append(CompanyVacancy.user_id == company_id)
    if status is not None:
        conditions.append(CompanyVacancy.status == status)
    if posted_from is not None:
        conditions.append(CompanyVacancy.created_at >= posted_from)
    if posted_to is not None:
        conditions.append(CompanyVacancy.created_at <= posted_to)
    if search:
        conditions.append(CompanyVacancy.vacancy_name.ilike(f"%{search}%"))

    return conditions


@companies_router.get("", response_model=CompanyListResponse)
async def list_companies(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None, description="Search companies by name"),
    sort_by: str = Query("created_at", description="Field to sort companies by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> CompanyListResponse:
    filters: list[sa.ColumnElement[bool]] = [
        User.role == UserRole.COMPANY,
        User.is_active.is_(True),
    ]
    if search:
        filters.append(CompanyProfile.company_name.ilike(f"%{search}%"))

    total_stmt = (
        sa.select(sa.func.count())
        .select_from(CompanyProfile)
        .join(User, User.id == CompanyProfile.user_id)
        .where(*filters)
    )
    total = db.scalar(total_stmt) or 0

    sort_clause = _build_sort_clause(
        sort_by,
        sort_order,
        {
            "created_at": CompanyProfile.created_at,
            "updated_at": CompanyProfile.updated_at,
            "company_name": CompanyProfile.company_name,
        },
    )

    stmt = (
        sa.select(CompanyProfile)
        .join(User, User.id == CompanyProfile.user_id)
        .where(*filters)
        .order_by(sort_clause)
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())

    return CompanyListResponse(items=items, total=total, limit=limit, offset=offset)


@companies_router.get("/{company_id}", response_model=CompanyProfileResponse)
async def get_public_company(
    company_id: UUID,
    db: Session = Depends(get_db),
) -> CompanyProfile:
    user = _ensure_company_user(db, company_id)
    profile = _get_company_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return profile


@companies_router.get("/{company_id}/vacancies", response_model=VacancyListResponse)
async def list_public_company_vacancies(
    company_id: UUID,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, description="Filter vacancies by status"),
    posted_from: datetime | None = Query(None, description="Filter vacancies created after this date"),
    posted_to: datetime | None = Query(None, description="Filter vacancies created before this date"),
    search: str | None = Query(None, description="Search vacancies by name"),
    sort_by: str = Query("created_at", description="Field to sort vacancies by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> VacancyListResponse:
    _ensure_company_user(db, company_id)
    resolved_status = _resolve_status_filter(status)

    conditions = _vacancy_filters(company_id, resolved_status, posted_from, posted_to, search)

    total_stmt = sa.select(sa.func.count()).select_from(CompanyVacancy).where(*conditions)
    total = db.scalar(total_stmt) or 0

    sort_clause = _build_sort_clause(
        sort_by,
        sort_order,
        {
            "created_at": CompanyVacancy.created_at,
            "updated_at": CompanyVacancy.updated_at,
            "vacancy_name": CompanyVacancy.vacancy_name,
            "status": CompanyVacancy.status,
        },
    )

    stmt = (
        sa.select(CompanyVacancy)
        .where(*conditions)
        .order_by(sort_clause)
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())

    return VacancyListResponse(items=items, total=total, limit=limit, offset=offset)


@companies_router.get("/{company_id}/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_public_vacancy(
    company_id: UUID,
    vacancy_id: UUID,
    db: Session = Depends(get_db),
) -> CompanyVacancy:
    _ensure_company_user(db, company_id)
    stmt = (
        sa.select(CompanyVacancy)
        .where(
            CompanyVacancy.user_id == company_id,
            CompanyVacancy.id == vacancy_id,
            CompanyVacancy.status != VacancyStatus.DRAFT,
        )
        .limit(1)
    )
    vacancy = db.scalar(stmt)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy not found")
    return vacancy


@vacancies_router.get("", response_model=VacancyListResponse)
async def list_public_vacancies(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, description="Filter vacancies by status"),
    company_id: UUID | None = Query(None, description="Filter vacancies by company identifier"),
    posted_from: datetime | None = Query(None, description="Filter vacancies created after this date"),
    posted_to: datetime | None = Query(None, description="Filter vacancies created before this date"),
    search: str | None = Query(None, description="Search vacancies by name"),
    sort_by: str = Query("created_at", description="Field to sort vacancies by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
) -> VacancyListResponse:
    resolved_status = _resolve_status_filter(status)

    conditions = _vacancy_filters(company_id, resolved_status, posted_from, posted_to, search)

    total_stmt = sa.select(sa.func.count()).select_from(CompanyVacancy).where(*conditions)
    total = db.scalar(total_stmt) or 0

    sort_clause = _build_sort_clause(
        sort_by,
        sort_order,
        {
            "created_at": CompanyVacancy.created_at,
            "updated_at": CompanyVacancy.updated_at,
            "vacancy_name": CompanyVacancy.vacancy_name,
            "status": CompanyVacancy.status,
        },
    )

    stmt = (
        sa.select(CompanyVacancy)
        .where(*conditions)
        .order_by(sort_clause)
        .offset(offset)
        .limit(limit)
    )
    items = list(db.scalars(stmt).all())

    return VacancyListResponse(items=items, total=total, limit=limit, offset=offset)


router = APIRouter()
router.include_router(me_router)
router.include_router(companies_router)
router.include_router(vacancies_router)
