from __future__ import annotations

import secrets
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from api.deps import get_db
from api.deps.auth import require_role
from api.schemas.internships import (
    EducationInternshipCreate,
    EducationInternshipListResponse,
    EducationInternshipResponse,
    EducationInternshipUpdate,
    EducationInternshipWithParticipantsResponse,
    InternshipCodeGenerateRequest,
    InternshipCodeResponse,
    InternshipEngagementCreateRequest,
    InternshipEngagementListResponse,
    InternshipParticipantResponse,
    InternshipParticipantUpdate,
    CompanyInternshipEngagementResponse,
    EducationInternshipEngagementResponse,
)
from api.schemas.profile import (
    ApplicantProfileResponse,
    CompanyProfileResponse,
    EducationProfileResponse,
)
from database.schema.base import (
    ApplicantProfile,
    CompanyProfile,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipEngagement,
    EducationInternshipMember,
    EducationInternshipStatus,
    EducationProfile,
    InternshipEngagementInitiator,
    InternshipEngagementStatus,
    InternshipParticipantStatus,
    User,
    UserRole,
)


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 10


router = APIRouter(prefix="/me/education/internships", tags=["Education Internships"])
company_internships_router = APIRouter(prefix="/company/internships", tags=["Company Internships"])


def _get_internship(db: Session, user_id: UUID, internship_id: UUID) -> EducationInternship:
    stmt = sa.select(EducationInternship).where(
        EducationInternship.id == internship_id,
        EducationInternship.user_id == user_id,
    )
    internship = db.scalar(stmt)
    if internship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship list not found")
    return internship


def _generate_code_value() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _validate_dates(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must not be earlier than start date",
        )


def _change_internship_status(
    db: Session, internship: EducationInternship, new_status: EducationInternshipStatus
) -> EducationInternship:
    internship.status = new_status
    db.add(internship)
    db.commit()
    db.refresh(internship)
    return internship


def _serialize_member(
    db: Session,
    member: EducationInternshipMember,
    user: User | None = None,
    profile: ApplicantProfile | None = None,
) -> InternshipParticipantResponse:
    resolved_user = user or db.get(User, member.user_id)
    resolved_profile = profile
    if resolved_profile is None:
        profile_stmt = sa.select(ApplicantProfile).where(ApplicantProfile.user_id == member.user_id)
        resolved_profile = db.scalar(profile_stmt)
    return InternshipParticipantResponse(
        id=member.id,
        internship_id=member.internship_id,
        user_id=member.user_id,
        status=member.status,
        created_at=member.created_at,
        updated_at=member.updated_at,
        email=resolved_user.email if resolved_user else "",
        profile=ApplicantProfileResponse.model_validate(resolved_profile) if resolved_profile else None,
    )


def _serialize_education_engagement(
    engagement: EducationInternshipEngagement,
    company_user: User,
    profile: CompanyProfile | None,
) -> EducationInternshipEngagementResponse:
    return EducationInternshipEngagementResponse(
        id=engagement.id,
        internship_id=engagement.internship_id,
        company_id=engagement.company_id,
        initiator=engagement.initiator,
        status=engagement.status,
        created_at=engagement.created_at,
        updated_at=engagement.updated_at,
        company_email=company_user.email,
        company_profile=(
            CompanyProfileResponse.model_validate(profile) if profile else None
        ),
    )


def _serialize_company_engagement(
    engagement: EducationInternshipEngagement,
    internship: EducationInternship,
    education_user: User,
    education_profile: EducationProfile | None,
) -> CompanyInternshipEngagementResponse:
    return CompanyInternshipEngagementResponse(
        id=engagement.id,
        internship_id=engagement.internship_id,
        company_id=engagement.company_id,
        initiator=engagement.initiator,
        status=engagement.status,
        created_at=engagement.created_at,
        updated_at=engagement.updated_at,
        education_email=education_user.email,
        education_profile=(
            EducationProfileResponse.model_validate(education_profile)
            if education_profile
            else None
        ),
        internship=EducationInternshipResponse.model_validate(internship),
    )


def _get_company_user(
    db: Session,
    company_id: UUID,
) -> tuple[User, CompanyProfile | None]:
    stmt = (
        sa.select(User, CompanyProfile)
        .join(CompanyProfile, CompanyProfile.user_id == User.id, isouter=True)
        .where(
            User.id == company_id,
            User.role == UserRole.COMPANY,
            User.is_active.is_(True),
        )
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return row


def _get_engagement_for_education(
    db: Session,
    internship_id: UUID,
    engagement_id: UUID,
) -> tuple[EducationInternshipEngagement, User, CompanyProfile | None]:
    stmt = (
        sa.select(EducationInternshipEngagement, User, CompanyProfile)
        .join(User, User.id == EducationInternshipEngagement.company_id)
        .join(
            CompanyProfile,
            CompanyProfile.user_id == User.id,
            isouter=True,
        )
        .where(
            EducationInternshipEngagement.internship_id == internship_id,
            EducationInternshipEngagement.id == engagement_id,
        )
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found")
    return row


def _get_engagement_for_company(
    db: Session,
    company_id: UUID,
    internship_id: UUID,
    engagement_id: UUID,
) -> tuple[
    EducationInternshipEngagement,
    EducationInternship,
    User,
    EducationProfile | None,
]:
    stmt = (
        sa.select(EducationInternshipEngagement, EducationInternship, User, EducationProfile)
        .join(
            EducationInternship,
            EducationInternship.id == EducationInternshipEngagement.internship_id,
        )
        .join(User, User.id == EducationInternship.user_id)
        .join(
            EducationProfile,
            EducationProfile.user_id == User.id,
            isouter=True,
        )
        .where(
            EducationInternshipEngagement.company_id == company_id,
            EducationInternshipEngagement.internship_id == internship_id,
            EducationInternshipEngagement.id == engagement_id,
        )
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Engagement not found")
    return row


def _list_education_engagements(
    db: Session,
    internship_id: UUID,
    limit: int,
    offset: int,
    status_filter: InternshipEngagementStatus | None,
) -> InternshipEngagementListResponse:
    filters: list[sa.ColumnElement[bool]] = [
        EducationInternshipEngagement.internship_id == internship_id
    ]
    if status_filter is not None:
        filters.append(EducationInternshipEngagement.status == status_filter)

    total_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternshipEngagement)
        .where(*filters)
    )
    total = db.scalar(total_stmt) or 0

    stmt = (
        sa.select(EducationInternshipEngagement, User, CompanyProfile)
        .join(User, User.id == EducationInternshipEngagement.company_id)
        .join(CompanyProfile, CompanyProfile.user_id == User.id, isouter=True)
        .where(*filters)
        .order_by(EducationInternshipEngagement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [
        _serialize_education_engagement(engagement, company_user, profile)
        for engagement, company_user, profile in rows
    ]
    return InternshipEngagementListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


def _list_company_engagements(
    db: Session,
    company_id: UUID,
    limit: int,
    offset: int,
    status_filter: InternshipEngagementStatus | None,
    internship_id: UUID | None = None,
) -> InternshipEngagementListResponse:
    filters: list[sa.ColumnElement[bool]] = [
        EducationInternshipEngagement.company_id == company_id
    ]
    if internship_id is not None:
        filters.append(EducationInternshipEngagement.internship_id == internship_id)
    if status_filter is not None:
        filters.append(EducationInternshipEngagement.status == status_filter)

    total_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternshipEngagement)
        .where(*filters)
    )
    total = db.scalar(total_stmt) or 0

    stmt = (
        sa.select(EducationInternshipEngagement, EducationInternship, User, EducationProfile)
        .join(
            EducationInternship,
            EducationInternship.id == EducationInternshipEngagement.internship_id,
        )
        .join(User, User.id == EducationInternship.user_id)
        .join(
            EducationProfile,
            EducationProfile.user_id == User.id,
            isouter=True,
        )
        .where(*filters)
        .order_by(EducationInternshipEngagement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    items = [
        _serialize_company_engagement(engagement, internship, education_user, profile)
        for engagement, internship, education_user, profile in rows
    ]
    return InternshipEngagementListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


def _ensure_pending_engagement(engagement: EducationInternshipEngagement) -> None:
    if engagement.status == InternshipEngagementStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Engagement was cancelled")
    if engagement.status == InternshipEngagementStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Engagement already approved")
    if engagement.status == InternshipEngagementStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Engagement already rejected")
    if engagement.status != InternshipEngagementStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Engagement is not pending")


@router.get("", response_model=list[EducationInternshipResponse])
async def list_internships(
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> list[EducationInternshipResponse]:
    stmt = (
        sa.select(EducationInternship)
        .where(EducationInternship.user_id == user.id)
        .order_by(EducationInternship.created_at.desc())
    )
    internships = db.scalars(stmt).all()
    return [EducationInternshipResponse.model_validate(item) for item in internships]


@router.post("", response_model=EducationInternshipResponse, status_code=status.HTTP_201_CREATED)
async def create_internship(
    payload: EducationInternshipCreate,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipResponse:
    _validate_dates(payload.start_date, payload.end_date)
    internship = EducationInternship(user_id=user.id, **payload.model_dump())
    db.add(internship)
    db.commit()
    db.refresh(internship)
    return EducationInternshipResponse.model_validate(internship)


@router.get("/{internship_id}", response_model=EducationInternshipResponse)
async def get_internship(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipResponse:
    internship = _get_internship(db, user.id, internship_id)
    return EducationInternshipResponse.model_validate(internship)


@router.put("/{internship_id}", response_model=EducationInternshipResponse)
async def update_internship(
    internship_id: UUID,
    payload: EducationInternshipUpdate,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipResponse:
    internship = _get_internship(db, user.id, internship_id)
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if update_data:
        new_start = update_data.get("start_date", internship.start_date)
        new_end = update_data.get("end_date", internship.end_date)
        _validate_dates(new_start, new_end)
    for field, value in update_data.items():
        setattr(internship, field, value)

    db.add(internship)
    db.commit()
    db.refresh(internship)
    return EducationInternshipResponse.model_validate(internship)


@router.post("/{internship_id}/publish", response_model=EducationInternshipResponse)
async def publish_internship(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipResponse:
    internship = _get_internship(db, user.id, internship_id)
    if internship.status != EducationInternshipStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft internships can be published",
        )
    updated = _change_internship_status(db, internship, EducationInternshipStatus.PUBLISHED)
    return EducationInternshipResponse.model_validate(updated)


@router.post("/{internship_id}/hide", response_model=EducationInternshipResponse)
async def hide_internship(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipResponse:
    internship = _get_internship(db, user.id, internship_id)
    if internship.status != EducationInternshipStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published internships can be hidden",
        )
    updated = _change_internship_status(db, internship, EducationInternshipStatus.DRAFT)
    return EducationInternshipResponse.model_validate(updated)


@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_internship(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> Response:
    internship = _get_internship(db, user.id, internship_id)
    db.delete(internship)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{internship_id}/codes",
    response_model=list[InternshipCodeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_codes(
    internship_id: UUID,
    payload: InternshipCodeGenerateRequest,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> list[InternshipCodeResponse]:
    internship = _get_internship(db, user.id, internship_id)

    expires_at = datetime.now(timezone.utc) + timedelta(days=2)
    created_codes: list[EducationInternshipCode] = []
    while len(created_codes) < payload.count:
        code_value = _generate_code_value()
        exists_stmt = sa.select(sa.literal(True)).where(EducationInternshipCode.code == code_value)
        if db.scalar(exists_stmt):
            continue
        code = EducationInternshipCode(
            internship_id=internship.id,
            code=code_value,
            expires_at=expires_at,
        )
        db.add(code)
        created_codes.append(code)

    db.commit()
    for code in created_codes:
        db.refresh(code)
    return [InternshipCodeResponse.model_validate(code) for code in created_codes]


@router.get("/{internship_id}/codes", response_model=list[InternshipCodeResponse])
async def list_codes(
    internship_id: UUID,
    active_only: bool = Query(False, description="Return only active codes"),
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> list[InternshipCodeResponse]:
    _get_internship(db, user.id, internship_id)

    stmt = sa.select(EducationInternshipCode).where(EducationInternshipCode.internship_id == internship_id)
    if active_only:
        now = datetime.now(timezone.utc)
        stmt = stmt.where(
            EducationInternshipCode.revoked_at.is_(None),
            EducationInternshipCode.used_at.is_(None),
            EducationInternshipCode.expires_at > now,
        )
    stmt = stmt.order_by(EducationInternshipCode.created_at.desc())
    codes = db.scalars(stmt).all()
    return [InternshipCodeResponse.model_validate(code) for code in codes]


@router.delete("/{internship_id}/codes/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_code(
    internship_id: UUID,
    code_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> Response:
    _get_internship(db, user.id, internship_id)
    code = db.get(EducationInternshipCode, code_id)
    if code is None or code.internship_id != internship_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Code not found")
    if code.used_at is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code already used")
    if code.revoked_at is not None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    code.revoked_at = datetime.now(timezone.utc)
    db.add(code)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{internship_id}/codes/download")
async def download_codes(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    _get_internship(db, user.id, internship_id)
    now = datetime.now(timezone.utc)
    stmt = sa.select(EducationInternshipCode).where(
        EducationInternshipCode.internship_id == internship_id,
        EducationInternshipCode.revoked_at.is_(None),
        EducationInternshipCode.used_at.is_(None),
        EducationInternshipCode.expires_at > now,
    )
    stmt = stmt.order_by(EducationInternshipCode.created_at.asc())
    codes = db.scalars(stmt).all()
    content = "\n".join(code.code for code in codes)
    filename = f"internship-{internship_id}-codes.txt"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return PlainTextResponse(content=content, headers=headers)


@router.get("/{internship_id}/participants", response_model=list[InternshipParticipantResponse])
async def list_participants(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> list[InternshipParticipantResponse]:
    internship = _get_internship(db, user.id, internship_id)
    stmt = (
        sa.select(EducationInternshipMember)
        .where(EducationInternshipMember.internship_id == internship.id)
        .order_by(EducationInternshipMember.created_at.desc())
    )
    members = db.scalars(stmt).all()
    return [_serialize_member(db, member) for member in members]


@router.patch(
    "/{internship_id}/participants/{participant_id}",
    response_model=InternshipParticipantResponse,
)
async def update_participant(
    internship_id: UUID,
    participant_id: UUID,
    payload: InternshipParticipantUpdate,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> InternshipParticipantResponse:
    _get_internship(db, user.id, internship_id)
    stmt = sa.select(EducationInternshipMember).where(
        EducationInternshipMember.id == participant_id,
        EducationInternshipMember.internship_id == internship_id,
    )
    member = db.scalar(stmt)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    member.status = payload.status
    db.add(member)
    db.commit()
    db.refresh(member)
    return _serialize_member(db, member)


@router.get(
    "/{internship_id}/responses",
    response_model=InternshipEngagementListResponse,
)
async def list_internship_engagements(
    internship_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: InternshipEngagementStatus | None = Query(
        None, alias="status", description="Filter engagements by status"
    ),
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> InternshipEngagementListResponse:
    internship = _get_internship(db, user.id, internship_id)
    return _list_education_engagements(db, internship.id, limit, offset, status_filter)


@router.post(
    "/{internship_id}/responses",
    response_model=EducationInternshipEngagementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_internship_engagement(
    internship_id: UUID,
    payload: InternshipEngagementCreateRequest,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipEngagementResponse:
    internship = _get_internship(db, user.id, internship_id)
    if internship.status != EducationInternshipStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only published internships can be shared",
        )

    company_user, company_profile = _get_company_user(db, payload.company_id)

    stmt = sa.select(EducationInternshipEngagement).where(
        EducationInternshipEngagement.internship_id == internship.id,
        EducationInternshipEngagement.company_id == company_user.id,
    )
    engagement = db.scalar(stmt)

    if engagement is None:
        engagement = EducationInternshipEngagement(
            internship_id=internship.id,
            company_id=company_user.id,
            initiator=InternshipEngagementInitiator.EDUCATION,
            status=InternshipEngagementStatus.PENDING,
        )
    elif engagement.status in {
        InternshipEngagementStatus.CANCELLED,
        InternshipEngagementStatus.REJECTED,
    }:
        engagement.status = InternshipEngagementStatus.PENDING
        engagement.initiator = InternshipEngagementInitiator.EDUCATION
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engagement already exists",
        )

    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_education_engagement(engagement, company_user, company_profile)


@router.post(
    "/{internship_id}/responses/{engagement_id}/cancel",
    response_model=EducationInternshipEngagementResponse,
)
async def cancel_internship_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipEngagementResponse:
    internship = _get_internship(db, user.id, internship_id)
    engagement, company_user, company_profile = _get_engagement_for_education(
        db, internship.id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.EDUCATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only engagements initiated by the education organization can be cancelled",
        )

    if engagement.status != InternshipEngagementStatus.CANCELLED:
        engagement.status = InternshipEngagementStatus.CANCELLED
        db.add(engagement)
        db.commit()
        db.refresh(engagement)

    return _serialize_education_engagement(engagement, company_user, company_profile)


@router.post(
    "/{internship_id}/responses/{engagement_id}/approve",
    response_model=EducationInternshipEngagementResponse,
)
async def approve_company_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipEngagementResponse:
    internship = _get_internship(db, user.id, internship_id)
    engagement, company_user, company_profile = _get_engagement_for_education(
        db, internship.id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.COMPANY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only company-initiated engagements can be approved",
        )
    _ensure_pending_engagement(engagement)
    engagement.status = InternshipEngagementStatus.APPROVED
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_education_engagement(engagement, company_user, company_profile)


@router.post(
    "/{internship_id}/responses/{engagement_id}/reject",
    response_model=EducationInternshipEngagementResponse,
)
async def reject_company_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.EDUCATION)),
    db: Session = Depends(get_db),
) -> EducationInternshipEngagementResponse:
    internship = _get_internship(db, user.id, internship_id)
    engagement, company_user, company_profile = _get_engagement_for_education(
        db, internship.id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.COMPANY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only company-initiated engagements can be rejected",
        )
    _ensure_pending_engagement(engagement)
    engagement.status = InternshipEngagementStatus.REJECTED
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_education_engagement(engagement, company_user, company_profile)


def _resolve_status_filter(status: str | None) -> EducationInternshipStatus | None:
    if status is None:
        return None
    try:
        resolved = EducationInternshipStatus(status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status") from exc
    if resolved == EducationInternshipStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft internships are not accessible")
    return resolved


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


def _internship_filters(
    education_id: UUID | None,
    status: EducationInternshipStatus | None,
    posted_from: datetime | None,
    posted_to: datetime | None,
    search: str | None,
) -> list[sa.ColumnElement[bool]]:
    conditions: list[sa.ColumnElement[bool]] = []

    if status is None:
        conditions.append(EducationInternship.status == EducationInternshipStatus.PUBLISHED)
    else:
        conditions.append(EducationInternship.status == status)

    if education_id is not None:
        conditions.append(EducationInternship.user_id == education_id)
    if posted_from is not None:
        conditions.append(EducationInternship.created_at >= posted_from)
    if posted_to is not None:
        conditions.append(EducationInternship.created_at <= posted_to)
    if search:
        conditions.append(EducationInternship.title.ilike(f"%{search}%"))

    return conditions


@company_internships_router.get("", response_model=EducationInternshipListResponse)
async def list_company_internships(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None, description="Filter internships by status"),
    education_id: UUID | None = Query(None, description="Filter internships by education identifier"),
    posted_from: datetime | None = Query(None, description="Filter internships created after this date"),
    posted_to: datetime | None = Query(None, description="Filter internships created before this date"),
    search: str | None = Query(None, description="Search internships by title"),
    sort_by: str = Query("created_at", description="Field to sort internships by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> EducationInternshipListResponse:
    resolved_status = _resolve_status_filter(status)

    conditions = _internship_filters(education_id, resolved_status, posted_from, posted_to, search)

    total_stmt = sa.select(sa.func.count()).select_from(EducationInternship).where(*conditions)
    total = db.scalar(total_stmt) or 0

    sort_clause = _build_sort_clause(
        sort_by,
        sort_order,
        {
            "created_at": EducationInternship.created_at,
            "updated_at": EducationInternship.updated_at,
            "title": EducationInternship.title,
            "start_date": EducationInternship.start_date,
            "end_date": EducationInternship.end_date,
            "status": EducationInternship.status,
        },
    )

    stmt = (
        sa.select(EducationInternship)
        .where(*conditions)
        .order_by(sort_clause)
        .offset(offset)
        .limit(limit)
    )
    internships = list(db.scalars(stmt).all())

    participants_map: dict[UUID, list[InternshipParticipantResponse]] = defaultdict(list)
    if internships:
        internship_ids = [internship.id for internship in internships]
        participants_stmt = (
            sa.select(EducationInternshipMember, User, ApplicantProfile)
            .join(User, User.id == EducationInternshipMember.user_id)
            .join(
                ApplicantProfile,
                ApplicantProfile.user_id == EducationInternshipMember.user_id,
                isouter=True,
            )
            .where(
                EducationInternshipMember.internship_id.in_(internship_ids),
                EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
            )
            .order_by(EducationInternshipMember.created_at.desc())
        )
        for member, participant_user, profile in db.execute(participants_stmt).all():
            participants_map[member.internship_id].append(
                _serialize_member(db, member, participant_user, profile)
            )

    items = []
    for internship in internships:
        base = EducationInternshipResponse.model_validate(internship)
        items.append(
            EducationInternshipWithParticipantsResponse(
                **base.model_dump(),
                approved_participants=participants_map.get(internship.id, []),
            )
        )

    return EducationInternshipListResponse(items=items, total=total, limit=limit, offset=offset)


@company_internships_router.get(
    "/{internship_id}", response_model=EducationInternshipWithParticipantsResponse
)
async def get_company_internship(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> EducationInternshipWithParticipantsResponse:
    stmt = sa.select(EducationInternship).where(
        EducationInternship.id == internship_id,
        EducationInternship.status == EducationInternshipStatus.PUBLISHED,
    )
    internship = db.scalar(stmt)
    if internship is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")

    participants_stmt = (
        sa.select(EducationInternshipMember, User, ApplicantProfile)
        .join(User, User.id == EducationInternshipMember.user_id)
        .join(
            ApplicantProfile,
            ApplicantProfile.user_id == EducationInternshipMember.user_id,
            isouter=True,
        )
        .where(
            EducationInternshipMember.internship_id == internship.id,
            EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
        )
        .order_by(EducationInternshipMember.created_at.desc())
    )

    participants = [
        _serialize_member(db, member, participant_user, profile)
        for member, participant_user, profile in db.execute(participants_stmt).all()
    ]

    base = EducationInternshipResponse.model_validate(internship)
    return EducationInternshipWithParticipantsResponse(
        **base.model_dump(),
        approved_participants=participants,
    )


@company_internships_router.get(
    "/responses",
    response_model=InternshipEngagementListResponse,
)
async def list_company_engagements_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: InternshipEngagementStatus | None = Query(
        None, alias="status", description="Filter engagements by status"
    ),
    internship_id: UUID | None = Query(
        None, description="Filter engagements by internship"
    ),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> InternshipEngagementListResponse:
    return _list_company_engagements(
        db,
        user.id,
        limit,
        offset,
        status_filter,
        internship_id,
    )


@company_internships_router.get(
    "/{internship_id}/responses",
    response_model=InternshipEngagementListResponse,
)
async def list_company_internship_engagements(
    internship_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: InternshipEngagementStatus | None = Query(
        None, alias="status", description="Filter engagements by status"
    ),
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> InternshipEngagementListResponse:
    return _list_company_engagements(
        db,
        user.id,
        limit,
        offset,
        status_filter,
        internship_id,
    )


@company_internships_router.post(
    "/{internship_id}/responses",
    response_model=CompanyInternshipEngagementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_engagement(
    internship_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyInternshipEngagementResponse:
    stmt = (
        sa.select(EducationInternship, User, EducationProfile)
        .join(User, User.id == EducationInternship.user_id)
        .join(EducationProfile, EducationProfile.user_id == User.id, isouter=True)
        .where(
            EducationInternship.id == internship_id,
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
        )
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found")

    internship, education_user, education_profile = row

    stmt = sa.select(EducationInternshipEngagement).where(
        EducationInternshipEngagement.internship_id == internship.id,
        EducationInternshipEngagement.company_id == user.id,
    )
    engagement = db.scalar(stmt)

    if engagement is None:
        engagement = EducationInternshipEngagement(
            internship_id=internship.id,
            company_id=user.id,
            initiator=InternshipEngagementInitiator.COMPANY,
            status=InternshipEngagementStatus.PENDING,
        )
    elif engagement.status in {
        InternshipEngagementStatus.CANCELLED,
        InternshipEngagementStatus.REJECTED,
    }:
        engagement.status = InternshipEngagementStatus.PENDING
        engagement.initiator = InternshipEngagementInitiator.COMPANY
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Engagement already exists",
        )

    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_company_engagement(
        engagement,
        internship,
        education_user,
        education_profile,
    )


@company_internships_router.post(
    "/{internship_id}/responses/{engagement_id}/cancel",
    response_model=CompanyInternshipEngagementResponse,
)
async def cancel_company_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyInternshipEngagementResponse:
    engagement, internship, education_user, education_profile = _get_engagement_for_company(
        db, user.id, internship_id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.COMPANY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only engagements initiated by the company can be cancelled",
        )

    if engagement.status != InternshipEngagementStatus.CANCELLED:
        engagement.status = InternshipEngagementStatus.CANCELLED
        db.add(engagement)
        db.commit()
        db.refresh(engagement)

    return _serialize_company_engagement(
        engagement,
        internship,
        education_user,
        education_profile,
    )


@company_internships_router.post(
    "/{internship_id}/responses/{engagement_id}/approve",
    response_model=CompanyInternshipEngagementResponse,
)
async def approve_education_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyInternshipEngagementResponse:
    engagement, internship, education_user, education_profile = _get_engagement_for_company(
        db, user.id, internship_id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.EDUCATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only education-initiated engagements can be approved",
        )
    _ensure_pending_engagement(engagement)
    engagement.status = InternshipEngagementStatus.APPROVED
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_company_engagement(
        engagement,
        internship,
        education_user,
        education_profile,
    )


@company_internships_router.post(
    "/{internship_id}/responses/{engagement_id}/reject",
    response_model=CompanyInternshipEngagementResponse,
)
async def reject_education_engagement(
    internship_id: UUID,
    engagement_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
    db: Session = Depends(get_db),
) -> CompanyInternshipEngagementResponse:
    engagement, internship, education_user, education_profile = _get_engagement_for_company(
        db, user.id, internship_id, engagement_id
    )
    if engagement.initiator != InternshipEngagementInitiator.EDUCATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only education-initiated engagements can be rejected",
        )
    _ensure_pending_engagement(engagement)
    engagement.status = InternshipEngagementStatus.REJECTED
    db.add(engagement)
    db.commit()
    db.refresh(engagement)
    return _serialize_company_engagement(
        engagement,
        internship,
        education_user,
        education_profile,
    )