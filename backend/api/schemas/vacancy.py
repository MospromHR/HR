from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from database.schema.base import VacancyStatus


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


class VacancyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    items: list[VacancyResponse]
    total: int
    limit: int
    offset: int
