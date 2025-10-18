from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicantProfileBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    bio: str | None = None
    contacts: dict[str, str] | None = None


class ApplicantProfileUpdate(ApplicantProfileBase):
    pass


class ApplicantProfileResponse(ApplicantProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime


class CompanyProfileBase(BaseModel):
    company_name: str | None = None
    description: str | None = None
    contacts: dict[str, str] | None = None


class CompanyProfileUpdate(CompanyProfileBase):
    pass


class CompanyProfileResponse(CompanyProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    logo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class EducationProfileBase(BaseModel):
    organization_name: str | None = None
    description: str | None = None
    contacts: dict[str, str] | None = None


class EducationProfileUpdate(EducationProfileBase):
    pass


class EducationProfileResponse(EducationProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    logo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class MediaUploadResponse(BaseModel):
    url: str
