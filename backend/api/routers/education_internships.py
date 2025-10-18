from __future__ import annotations

import secrets
import string
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
    EducationInternshipResponse,
    EducationInternshipUpdate,
    InternshipCodeGenerateRequest,
    InternshipCodeResponse,
    InternshipParticipantResponse,
    InternshipParticipantUpdate,
)
from api.schemas.profile import ApplicantProfileResponse
from database.schema.base import (
    ApplicantProfile,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipMember,
    User,
    UserRole,
)


CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 10


router = APIRouter(prefix="/me/education/internships", tags=["Education Internships"])


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


def _serialize_member(db: Session, member: EducationInternshipMember) -> InternshipParticipantResponse:
    user = db.get(User, member.user_id)
    profile_stmt = sa.select(ApplicantProfile).where(ApplicantProfile.user_id == member.user_id)
    profile = db.scalar(profile_stmt)
    return InternshipParticipantResponse(
        id=member.id,
        internship_id=member.internship_id,
        user_id=member.user_id,
        status=member.status,
        created_at=member.created_at,
        updated_at=member.updated_at,
        email=user.email if user else "",
        profile=ApplicantProfileResponse.model_validate(profile) if profile else None,
    )


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

