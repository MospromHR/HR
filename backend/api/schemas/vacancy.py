from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from api.schemas.profile import ApplicantProfileResponse
from database.schema.base import VacancyApplicationStatus, VacancyStatus


class VacancyBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    vacancy_name: str = Field(validation_alias="vacancyName", serialization_alias="vacancyName")
    speciality: str
    responsibilities: str
    requirements: str
    terms: str | None = None
    work_schedule: str | None = Field(
        default=None,
        validation_alias="workSchedule",
        serialization_alias="workSchedule",
    )
    work_place: str | None = Field(
        default=None,
        validation_alias="workPlace",
        serialization_alias="workPlace",
    )
    map_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("map", "mapUrl"),
        serialization_alias="map",
    )
    probation: str | None = None
    salary: str | None = None
    additionally: str | None = None
    task: str | None = None


class VacancyCreate(VacancyBase):
    pass


class VacancyResponse(VacancyBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    user_id: UUID = Field(serialization_alias="companyId")
    status: VacancyStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    applications_count: int = Field(serialization_alias="applicationsCount")


class VacancyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[VacancyResponse]
    total: int
    limit: int
    offset: int


class VacancyApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    vacancy_id: UUID = Field(serialization_alias="vacancyId")
    applicant_id: UUID = Field(serialization_alias="applicantId")
    status: VacancyApplicationStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ApplicantVacancyApplicationResponse(VacancyApplicationResponse):
    vacancy: VacancyResponse


class ApplicantVacancyApplicationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[ApplicantVacancyApplicationResponse]
    total: int
    limit: int
    offset: int


class CompanyVacancyApplicationResponse(VacancyApplicationResponse):
    applicant_email: str = Field(serialization_alias="applicantEmail")
    applicant_profile: ApplicantProfileResponse | None = Field(
        default=None,
        serialization_alias="applicantProfile",
    )
    vacancy: VacancyResponse


class CompanyVacancyApplicationListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[CompanyVacancyApplicationResponse]
    total: int
    limit: int
    offset: int
