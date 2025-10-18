from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_config, get_db, get_stats_cache
from api.deps.auth import require_role
from api.schemas.analytics import ApplicantStatsResponse
from api.schemas.internships import (
    ApplicantInternshipMembershipResponse,
    EducationInternshipResponse,
    InternshipActivationRequest,
)
from api.schemas.profile import (
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
    MediaUploadResponse,
)
from api.schemas.vacancy import (
    ApplicantVacancyApplicationListResponse,
    ApplicantVacancyApplicationResponse,
    VacancyResponse,
)
from api.schemas.user import RoleResponse
from api.services import SimpleTTLCache
from api.services.analytics import get_applicant_stats
from config import Config
from database.schema.base import (
    ApplicantProfile,
    CompanyVacancy,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipMember,
    EducationInternshipStatus,
    InternshipParticipantStatus,
    User,
    UserRole,
    VacancyApplication,
    VacancyApplicationStatus,
    VacancyStatus,
)

from ._media import save_media_file


router = APIRouter(prefix="/me", tags=["Applicants"])


def _get_applicant_profile(db: Session, user_id: UUID) -> ApplicantProfile | None:
    stmt = sa.select(ApplicantProfile).where(ApplicantProfile.user_id == user_id)
    return db.scalar(stmt)


def _serialize_membership(
    member: EducationInternshipMember, internship: EducationInternship
) -> ApplicantInternshipMembershipResponse:
    return ApplicantInternshipMembershipResponse(
        id=member.id,
        internship_id=member.internship_id,
        status=member.status,
        created_at=member.created_at,
        updated_at=member.updated_at,
        internship=EducationInternshipResponse.model_validate(internship),
    )


def _get_available_vacancy(db: Session, vacancy_id: UUID) -> CompanyVacancy:
    stmt = sa.select(CompanyVacancy).where(
        CompanyVacancy.id == vacancy_id,
        CompanyVacancy.status == VacancyStatus.PUBLISHED,
    )
    vacancy = db.scalar(stmt)
    if vacancy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vacancy is not available")
    return vacancy


def _serialize_applicant_application(
    application: VacancyApplication,
    vacancy: CompanyVacancy,
) -> ApplicantVacancyApplicationResponse:
    return ApplicantVacancyApplicationResponse(
        id=application.id,
        vacancy_id=application.vacancy_id,
        applicant_id=application.user_id,
        status=application.status,
        created_at=application.created_at,
        updated_at=application.updated_at,
        vacancy=VacancyResponse.model_validate(vacancy),
    )


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


@router.get("/applicant/stats", response_model=ApplicantStatsResponse)
async def get_applicant_stats_endpoint(
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
    cache: SimpleTTLCache[ApplicantStatsResponse] = Depends(get_stats_cache),
) -> ApplicantStatsResponse:
    cache_key = f"applicant-stats:{user.id}"
    return cache.get_or_set(cache_key, lambda: get_applicant_stats(db, user.id))


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
    cfg: Config = Depends(get_config),
) -> MediaUploadResponse:
    profile = _get_applicant_profile(db, user.id)
    if profile is None:
        profile = ApplicantProfile(user_id=user.id)
        db.add(profile)

    profile.avatar_url = save_media_file(
        avatar,
        f"applicants/{user.id}",
        profile.avatar_url,
        media_root=cfg.storage.media_root,
        public_prefix=cfg.storage.public_path_prefix,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return MediaUploadResponse(url=profile.avatar_url or "")


@router.get(
    "/applicant/internships",
    response_model=list[ApplicantInternshipMembershipResponse],
)
async def list_applicant_internships(
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> list[ApplicantInternshipMembershipResponse]:
    stmt = (
        sa.select(EducationInternshipMember, EducationInternship)
        .join(EducationInternship, EducationInternshipMember.internship_id == EducationInternship.id)
        .where(EducationInternshipMember.user_id == user.id)
        .order_by(EducationInternshipMember.created_at.desc())
    )
    result = db.execute(stmt).all()
    return [_serialize_membership(member, internship) for member, internship in result]


@router.post(
    "/applicant/internships/activate",
    response_model=ApplicantInternshipMembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def activate_internship_code(
    payload: InternshipActivationRequest,
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantInternshipMembershipResponse:
    code_value = payload.code.strip().upper()
    if not code_value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code must not be empty")
    now = datetime.now(timezone.utc)
    stmt = (
        sa.select(EducationInternshipCode, EducationInternship)
        .join(EducationInternship, EducationInternshipCode.internship_id == EducationInternship.id)
        .where(EducationInternshipCode.code == code_value)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code not found")

    code, internship = row
    if internship.status != EducationInternshipStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Internship is not available")
    if code.revoked_at is not None or code.used_at is not None or code.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code is not active")

    membership_stmt = sa.select(EducationInternshipMember).where(
        EducationInternshipMember.user_id == user.id,
        EducationInternshipMember.internship_id == internship.id,
    )
    membership = db.scalar(membership_stmt)
    if membership is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already participate in this internship",
        )

    count_stmt = sa.select(sa.func.count()).where(
        EducationInternshipMember.internship_id == internship.id,
        EducationInternshipMember.status.in_(
            [
                InternshipParticipantStatus.PENDING,
                InternshipParticipantStatus.APPROVED,
            ]
        ),
    )
    active_count = db.scalar(count_stmt) or 0
    if active_count >= internship.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Internship list is full")

    membership = EducationInternshipMember(
        internship_id=internship.id,
        user_id=user.id,
        status=InternshipParticipantStatus.PENDING,
    )
    code.used_at = now
    code.used_by_user_id = user.id

    db.add(membership)
    db.add(code)
    db.commit()
    db.refresh(membership)
    return _serialize_membership(membership, internship)


@router.delete(
    "/applicant/internships/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_internship(
    membership_id: UUID,
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> Response:
    stmt = sa.select(EducationInternshipMember).where(
        EducationInternshipMember.id == membership_id,
        EducationInternshipMember.user_id == user.id,
    )
    membership = db.scalar(stmt)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participation not found")

    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/applicant/vacancies/applications",
    response_model=ApplicantVacancyApplicationListResponse,
)
async def list_vacancy_applications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: VacancyApplicationStatus | None = Query(
        None, alias="status", description="Filter applications by status"
    ),
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantVacancyApplicationListResponse:
    filters: list[sa.ColumnElement[bool]] = [VacancyApplication.user_id == user.id]
    if status_filter is not None:
        filters.append(VacancyApplication.status == status_filter)

    total_stmt = sa.select(sa.func.count()).select_from(VacancyApplication).where(*filters)
    total = db.scalar(total_stmt) or 0

    stmt = (
        sa.select(VacancyApplication, CompanyVacancy)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(*filters)
        .order_by(VacancyApplication.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [
        _serialize_applicant_application(application, vacancy)
        for application, vacancy in rows
    ]

    return ApplicantVacancyApplicationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/applicant/vacancies/{vacancy_id}/applications",
    response_model=ApplicantVacancyApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_for_vacancy(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantVacancyApplicationResponse:
    vacancy = _get_available_vacancy(db, vacancy_id)
    stmt = sa.select(VacancyApplication).where(
        VacancyApplication.vacancy_id == vacancy.id,
        VacancyApplication.user_id == user.id,
    )
    application = db.scalar(stmt)

    if application is None:
        application = VacancyApplication(
            vacancy_id=vacancy.id,
            user_id=user.id,
            status=VacancyApplicationStatus.PENDING,
        )
    else:
        if application.status != VacancyApplicationStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied to this vacancy",
            )
        application.status = VacancyApplicationStatus.PENDING

    db.add(application)
    db.commit()
    db.refresh(application)
    return _serialize_applicant_application(application, vacancy)


@router.post(
    "/applicant/vacancies/{vacancy_id}/applications/cancel",
    response_model=ApplicantVacancyApplicationResponse,
)
async def cancel_vacancy_application(
    vacancy_id: UUID,
    user: User = Depends(require_role(UserRole.APPLICANT)),
    db: Session = Depends(get_db),
) -> ApplicantVacancyApplicationResponse:
    stmt = (
        sa.select(VacancyApplication, CompanyVacancy)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(
            VacancyApplication.vacancy_id == vacancy_id,
            VacancyApplication.user_id == user.id,
        )
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application, vacancy = row
    if application.status == VacancyApplicationStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application has already been reviewed",
        )

    if application.status != VacancyApplicationStatus.CANCELLED:
        application.status = VacancyApplicationStatus.CANCELLED
        db.add(application)
        db.commit()
        db.refresh(application)

    return _serialize_applicant_application(application, vacancy)
