from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from database.schema.base import (
    InternshipEngagementInitiator,
    InternshipEngagementStatus,
    InternshipParticipantStatus,
    VacancyApplicationStatus,
)


class SpecialityDistributionItem(BaseModel):
    speciality: str
    applications: int


class ApplicantStatsResponse(BaseModel):
    total_applications: int
    approved_applications: int
    rejected_applications: int
    cancelled_applications: int
    pending_applications: int
    conversion_rate: float
    pending_rate: float
    average_decision_time_days: float | None
    applications_last_30_days: int
    active_internships: int
    upcoming_internships: int
    nearest_upcoming_internship_days: float | None
    speciality_distribution: list[SpecialityDistributionItem]


class StatusCount(BaseModel):
    status: VacancyApplicationStatus
    count: int


class EngagementStatusCount(BaseModel):
    status: InternshipEngagementStatus
    count: int


class CompanyEngagementInitiatorCount(BaseModel):
    initiator: InternshipEngagementInitiator
    count: int


class CompanyStatsResponse(BaseModel):
    average_vacancy_closure_days: float | None
    accepted_students: int
    success_rate: float
    total_applications: int
    average_applications_per_vacancy: float | None
    application_status_breakdown: list[StatusCount]
    average_response_time_days: float | None
    published_vacancies: int
    open_vacancies: int
    engagements: list[EngagementStatusCount]
    engagements_by_initiator: list[CompanyEngagementInitiatorCount]
    approved_internship_average_duration_days: float | None
    current_approved_internships: int


class InternshipStatusOverview(BaseModel):
    active: int
    planned: int
    completed: int


class ParticipantStatusCount(BaseModel):
    status: InternshipParticipantStatus
    count: int


class EducationEngagementStatusCount(BaseModel):
    status: InternshipEngagementStatus
    count: int


class EducationEngagementInitiatorCount(BaseModel):
    initiator: InternshipEngagementInitiator
    count: int


class InviteActivity(BaseModel):
    active: int
    used: int
    expired: int


class EducationStatsResponse(BaseModel):
    internships: InternshipStatusOverview
    participants_total: int
    participants_by_status: list[ParticipantStatusCount]
    partner_companies: int
    capacity_utilization: float
    average_recruitment_days: float | None
    invite_activity: InviteActivity
    engagement_status_breakdown: list[EducationEngagementStatusCount]
    engagement_initiator_breakdown: list[EducationEngagementInitiatorCount]
    average_participant_course: float | None
    published_internships: int


class TimeSeriesPoint(BaseModel):
    month: date
    count: int


class InviteSummary(BaseModel):
    active: int
    used: int
    expired: int


class AdminStatsResponse(BaseModel):
    active_applicants: int
    active_companies: int
    active_educations: int
    active_internships: int
    employment_rate: float
    average_internship_duration_days: float | None
    company_growth_percent: float
    internship_series: list[TimeSeriesPoint]
    vacancy_series: list[TimeSeriesPoint]
    average_internship_fill_rate: float
    application_per_vacancy_ratio: float | None
    engagement_status_breakdown: list[EducationEngagementStatusCount]
    invite_summary: InviteSummary
