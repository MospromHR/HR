from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from database.schema.base import EducationInternshipStatus, InternshipParticipantStatus

from .profile import ApplicantProfileResponse


class EducationInternshipBase(BaseModel):
    title: str
    speciality_code: str
    start_date: date
    end_date: date
    capacity: int = Field(gt=0)
    type: str | None = None
    course: int | None = None
    description: str | None = None


class EducationInternshipCreate(EducationInternshipBase):
    pass


class EducationInternshipUpdate(BaseModel):
    title: str | None = None
    speciality_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = Field(default=None, gt=0)
    type: str | None = None
    course: int | None = None
    description: str | None = None


class EducationInternshipResponse(EducationInternshipBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: EducationInternshipStatus
    created_at: datetime
    updated_at: datetime


class InternshipCodeGenerateRequest(BaseModel):
    count: int = Field(gt=0, le=200)


class InternshipCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internship_id: UUID
    code: str
    expires_at: datetime
    created_at: datetime
    revoked_at: datetime | None
    used_at: datetime | None
    used_by_user_id: UUID | None


class InternshipParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    internship_id: UUID
    user_id: UUID
    status: InternshipParticipantStatus
    created_at: datetime
    updated_at: datetime
    email: str
    profile: ApplicantProfileResponse | None = None


class InternshipParticipantUpdate(BaseModel):
    status: InternshipParticipantStatus


class InternshipActivationRequest(BaseModel):
    code: str


class ApplicantInternshipMembershipResponse(BaseModel):
    id: UUID
    internship_id: UUID
    status: InternshipParticipantStatus
    created_at: datetime
    updated_at: datetime
    internship: EducationInternshipResponse


class EducationInternshipWithParticipantsResponse(EducationInternshipResponse):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    approved_participants: list[InternshipParticipantResponse] = Field(
        default_factory=list,
        validation_alias="approvedParticipants",
        serialization_alias="approvedParticipants",
    )


class EducationInternshipListResponse(BaseModel):
    items: list[EducationInternshipWithParticipantsResponse]
    total: int
    limit: int
    offset: int

