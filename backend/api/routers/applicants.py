from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session
from uuid import UUID

from api.deps import get_config, get_db
from api.deps.auth import require_role
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
from api.schemas.user import RoleResponse
from config import Config
from database.schema.base import (
    ApplicantProfile,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipMember,
    InternshipParticipantStatus,
    User,
    UserRole,
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
