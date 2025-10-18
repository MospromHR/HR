from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Session

from api.schemas.analytics import (
    AdminStatsResponse,
    ApplicantStatsResponse,
    CompanyEngagementInitiatorCount,
    CompanyStatsResponse,
    EducationEngagementInitiatorCount,
    EducationEngagementStatusCount,
    EducationStatsResponse,
    EngagementStatusCount,
    InviteActivity,
    InviteSummary,
    InternshipStatusOverview,
    ParticipantStatusCount,
    SpecialityDistributionItem,
    StatusCount,
    TimeSeriesPoint,
)
from database.schema.base import (
    CompanyVacancy,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipEngagement,
    EducationInternshipMember,
    EducationInternshipStatus,
    InternshipEngagementInitiator,
    InternshipEngagementStatus,
    InternshipParticipantStatus,
    User,
    UserRole,
    VacancyApplication,
    VacancyApplicationStatus,
    VacancyStatus,
)

SECONDS_IN_DAY = 60 * 60 * 24


def _as_days(seconds: float | None) -> float | None:
    if seconds is None:
        return None
    return round(seconds / SECONDS_IN_DAY, 2)


def _interval_to_days(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    if hasattr(value, "total_seconds"):
        return round(value.total_seconds() / SECONDS_IN_DAY, 2)
    return None


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _current_date() -> date:
    return _now_utc().date()


def _month_start_sequence(length: int) -> list[date]:
    current = _now_utc().date().replace(day=1)
    months: list[date] = []
    for _ in range(length):
        months.append(current)
        year = current.year
        month = current.month - 1
        if month == 0:
            month = 12
            year -= 1
        current = date(year, month, 1)
    months.reverse()
    return months


def get_applicant_stats(db: Session, user_id) -> ApplicantStatsResponse:
    status_counts_stmt = (
        sa.select(
            VacancyApplication.status,
            sa.func.count().label("count"),
        )
        .select_from(VacancyApplication)
        .where(VacancyApplication.user_id == user_id)
        .group_by(VacancyApplication.status)
    )
    status_counts = {row.status: row.count for row in db.execute(status_counts_stmt).all()}

    total_applications = sum(status_counts.values())
    approved = status_counts.get(VacancyApplicationStatus.APPROVED, 0)
    rejected = status_counts.get(VacancyApplicationStatus.REJECTED, 0)
    cancelled = status_counts.get(VacancyApplicationStatus.CANCELLED, 0)
    pending = status_counts.get(VacancyApplicationStatus.PENDING, 0)

    decision_time_stmt = (
        sa.select(
            sa.func.avg(
                sa.func.extract(
                    "epoch",
                    VacancyApplication.updated_at - VacancyApplication.created_at,
                )
            )
        )
        .select_from(VacancyApplication)
        .where(
            VacancyApplication.user_id == user_id,
            VacancyApplication.status != VacancyApplicationStatus.PENDING,
        )
    )
    avg_decision_seconds = db.scalar(decision_time_stmt)

    thirty_days_ago = _now_utc() - timedelta(days=30)
    applications_last_30_days_stmt = (
        sa.select(sa.func.count())
        .select_from(VacancyApplication)
        .where(
            VacancyApplication.user_id == user_id,
            VacancyApplication.created_at >= thirty_days_ago,
        )
    )
    applications_last_30_days = db.scalar(applications_last_30_days_stmt) or 0

    current_date = _current_date()
    active_internships_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternshipMember)
        .join(EducationInternship, EducationInternshipMember.internship_id == EducationInternship.id)
        .where(
            EducationInternshipMember.user_id == user_id,
            EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
            EducationInternship.start_date <= current_date,
            EducationInternship.end_date >= current_date,
        )
    )
    active_internships = db.scalar(active_internships_stmt) or 0

    upcoming_internships_stmt = (
        sa.select(
            sa.func.count().label("count"),
            sa.func.min(EducationInternship.start_date).label("nearest_start"),
        )
        .select_from(EducationInternshipMember)
        .join(EducationInternship, EducationInternshipMember.internship_id == EducationInternship.id)
        .where(
            EducationInternshipMember.user_id == user_id,
            EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
            EducationInternship.start_date > current_date,
        )
    )
    upcoming_row = db.execute(upcoming_internships_stmt).one()
    upcoming_count = upcoming_row.count or 0
    nearest_start = upcoming_row.nearest_start
    nearest_in_days = None
    if nearest_start is not None:
        nearest_in_days = (nearest_start - current_date).days

    speciality_stmt = (
        sa.select(CompanyVacancy.speciality, sa.func.count())
        .select_from(VacancyApplication)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(VacancyApplication.user_id == user_id)
        .group_by(CompanyVacancy.speciality)
        .order_by(sa.func.count().desc())
        .limit(5)
    )
    speciality_distribution = [
        SpecialityDistributionItem(speciality=row.speciality, applications=row.count)
        for row in db.execute(speciality_stmt).all()
    ]

    return ApplicantStatsResponse(
        total_applications=total_applications,
        approved_applications=approved,
        rejected_applications=rejected,
        cancelled_applications=cancelled,
        pending_applications=pending,
        conversion_rate=_safe_div(approved, total_applications),
        pending_rate=_safe_div(pending, total_applications),
        average_decision_time_days=_as_days(avg_decision_seconds),
        applications_last_30_days=applications_last_30_days,
        active_internships=active_internships,
        upcoming_internships=upcoming_count,
        nearest_upcoming_internship_days=float(nearest_in_days) if nearest_in_days is not None else None,
        speciality_distribution=speciality_distribution,
    )


def get_company_stats(db: Session, user_id) -> CompanyStatsResponse:
    vacancy_count_stmt = sa.select(sa.func.count()).select_from(CompanyVacancy).where(CompanyVacancy.user_id == user_id)
    vacancy_count = db.scalar(vacancy_count_stmt) or 0

    closure_stmt = (
        sa.select(
            sa.func.avg(
                sa.func.extract(
                    "epoch",
                    CompanyVacancy.updated_at - CompanyVacancy.created_at,
                )
            )
        )
        .select_from(CompanyVacancy)
        .where(
            CompanyVacancy.user_id == user_id,
            CompanyVacancy.status == VacancyStatus.CLOSED,
        )
    )
    avg_closure_seconds = db.scalar(closure_stmt)

    application_status_stmt = (
        sa.select(VacancyApplication.status, sa.func.count().label("count"))
        .select_from(VacancyApplication)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(CompanyVacancy.user_id == user_id)
        .group_by(VacancyApplication.status)
    )
    status_rows = db.execute(application_status_stmt).all()
    status_counts = {row.status: row.count for row in status_rows}
    total_applications = sum(status_counts.values())
    approved = status_counts.get(VacancyApplicationStatus.APPROVED, 0)

    average_applications_per_vacancy = round(total_applications / vacancy_count, 2) if vacancy_count else 0.0

    response_time_stmt = (
        sa.select(
            sa.func.avg(
                sa.func.extract(
                    "epoch",
                    VacancyApplication.updated_at - VacancyApplication.created_at,
                )
            )
        )
        .select_from(VacancyApplication)
        .join(CompanyVacancy, CompanyVacancy.id == VacancyApplication.vacancy_id)
        .where(
            CompanyVacancy.user_id == user_id,
            VacancyApplication.status != VacancyApplicationStatus.PENDING,
        )
    )
    avg_response_seconds = db.scalar(response_time_stmt)

    published_stmt = (
        sa.select(sa.func.count())
        .select_from(CompanyVacancy)
        .where(CompanyVacancy.user_id == user_id, CompanyVacancy.status == VacancyStatus.PUBLISHED)
    )
    published_vacancies = db.scalar(published_stmt) or 0

    engagement_status_stmt = (
        sa.select(
            EducationInternshipEngagement.status,
            sa.func.count().label("count"),
        )
        .select_from(EducationInternshipEngagement)
        .where(EducationInternshipEngagement.company_id == user_id)
        .group_by(EducationInternshipEngagement.status)
    )
    engagement_rows = db.execute(engagement_status_stmt).all()
    engagements = [
        EngagementStatusCount(status=row.status, count=row.count)
        for row in engagement_rows
    ]

    engagement_initiator_stmt = (
        sa.select(
            EducationInternshipEngagement.initiator,
            sa.func.count().label("count"),
        )
        .select_from(EducationInternshipEngagement)
        .where(EducationInternshipEngagement.company_id == user_id)
        .group_by(EducationInternshipEngagement.initiator)
    )
    engagement_initiator_rows = db.execute(engagement_initiator_stmt).all()
    engagements_by_initiator = [
        CompanyEngagementInitiatorCount(initiator=row.initiator, count=row.count)
        for row in engagement_initiator_rows
    ]

    approved_internships_stmt = (
        sa.select(EducationInternship.start_date, EducationInternship.end_date)
        .select_from(EducationInternshipEngagement)
        .join(EducationInternship, EducationInternship.id == EducationInternshipEngagement.internship_id)
        .where(
            EducationInternshipEngagement.company_id == user_id,
            EducationInternshipEngagement.status == InternshipEngagementStatus.APPROVED,
        )
    )
    approved_internships = db.execute(approved_internships_stmt).all()
    if approved_internships:
        durations_days = [
            (row.end_date - row.start_date).days
            for row in approved_internships
            if row.end_date is not None and row.start_date is not None
        ]
        avg_duration_days = round(sum(durations_days) / len(durations_days), 2) if durations_days else None
    else:
        avg_duration_days = None

    current_date = _current_date()
    current_approved_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternshipEngagement)
        .join(EducationInternship, EducationInternship.id == EducationInternshipEngagement.internship_id)
        .where(
            EducationInternshipEngagement.company_id == user_id,
            EducationInternshipEngagement.status == InternshipEngagementStatus.APPROVED,
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
            EducationInternship.start_date <= current_date,
            EducationInternship.end_date >= current_date,
        )
    )
    current_approved = db.scalar(current_approved_stmt) or 0

    return CompanyStatsResponse(
        average_vacancy_closure_days=_as_days(avg_closure_seconds),
        accepted_students=approved,
        success_rate=_safe_div(approved, total_applications),
        total_applications=total_applications,
        average_applications_per_vacancy=average_applications_per_vacancy,
        application_status_breakdown=[
            StatusCount(status=row.status, count=row.count) for row in status_rows
        ],
        average_response_time_days=_as_days(avg_response_seconds),
        published_vacancies=published_vacancies,
        open_vacancies=published_vacancies,
        engagements=engagements,
        engagements_by_initiator=engagements_by_initiator,
        approved_internship_average_duration_days=avg_duration_days,
        current_approved_internships=current_approved,
    )


def get_education_stats(db: Session, user_id) -> EducationStatsResponse:
    internships_stmt = sa.select(EducationInternship).where(EducationInternship.user_id == user_id)
    internships = list(db.scalars(internships_stmt))

    current_date = _current_date()
    active = 0
    planned = 0
    completed = 0
    total_capacity = 0
    recruitment_days: list[int] = []
    published_internships = 0
    for internship in internships:
        if internship.status == EducationInternshipStatus.PUBLISHED:
            published_internships += 1
            total_capacity += internship.capacity
            if internship.start_date <= current_date <= internship.end_date:
                active += 1
            elif internship.start_date > current_date:
                planned += 1
            elif internship.end_date < current_date:
                completed += 1
            if internship.created_at is not None:
                recruitment_days.append((internship.start_date - internship.created_at.date()).days)

    average_recruitment_days = (
        round(sum(recruitment_days) / len(recruitment_days), 2) if recruitment_days else None
    )

    participant_status_stmt = (
        sa.select(EducationInternshipMember.status, sa.func.count().label("count"))
        .select_from(EducationInternshipMember)
        .join(EducationInternship, EducationInternship.id == EducationInternshipMember.internship_id)
        .where(EducationInternship.user_id == user_id)
        .group_by(EducationInternshipMember.status)
    )
    participant_rows = db.execute(participant_status_stmt).all()
    participants_by_status = [
        ParticipantStatusCount(status=row.status, count=row.count)
        for row in participant_rows
    ]
    participants_total = sum(row.count for row in participant_rows)
    approved_participants = next(
        (row.count for row in participant_rows if row.status == InternshipParticipantStatus.APPROVED),
        0,
    )
    capacity_utilization = _safe_div(approved_participants, total_capacity) if total_capacity else 0.0

    partner_companies_stmt = (
        sa.select(sa.func.count(sa.distinct(EducationInternshipEngagement.company_id)))
        .select_from(EducationInternshipEngagement)
        .join(EducationInternship, EducationInternship.id == EducationInternshipEngagement.internship_id)
        .where(
            EducationInternship.user_id == user_id,
            EducationInternshipEngagement.status == InternshipEngagementStatus.APPROVED,
        )
    )
    partner_companies = db.scalar(partner_companies_stmt) or 0

    now = _now_utc()
    codes_stmt = (
        sa.select(
            sa.func.count(sa.case((
                sa.and_(
                    EducationInternshipCode.used_at.is_(None),
                    EducationInternshipCode.revoked_at.is_(None),
                    EducationInternshipCode.expires_at >= now,
                ),
                1,
            ))).label("active"),
            sa.func.count(sa.case((EducationInternshipCode.used_at.is_not(None), 1))).label("used"),
            sa.func.count(sa.case((
                sa.and_(
                    EducationInternshipCode.used_at.is_(None),
                    EducationInternshipCode.expires_at < now,
                ),
                1,
            ))).label("expired"),
        )
        .select_from(EducationInternshipCode)
        .join(EducationInternship, EducationInternship.id == EducationInternshipCode.internship_id)
        .where(EducationInternship.user_id == user_id)
    )
    codes_row = db.execute(codes_stmt).one()

    engagement_status_stmt = (
        sa.select(
            EducationInternshipEngagement.status,
            sa.func.count().label("count"),
        )
        .select_from(EducationInternshipEngagement)
        .join(EducationInternship, EducationInternship.id == EducationInternshipEngagement.internship_id)
        .where(EducationInternship.user_id == user_id)
        .group_by(EducationInternshipEngagement.status)
    )
    education_engagement_rows = db.execute(engagement_status_stmt).all()
    engagement_status_breakdown = [
        EducationEngagementStatusCount(status=row.status, count=row.count)
        for row in education_engagement_rows
    ]

    engagement_initiator_stmt = (
        sa.select(
            EducationInternshipEngagement.initiator,
            sa.func.count().label("count"),
        )
        .select_from(EducationInternshipEngagement)
        .join(EducationInternship, EducationInternship.id == EducationInternshipEngagement.internship_id)
        .where(EducationInternship.user_id == user_id)
        .group_by(EducationInternshipEngagement.initiator)
    )
    education_engagement_initiators = db.execute(engagement_initiator_stmt).all()
    engagement_initiator_breakdown = [
        EducationEngagementInitiatorCount(initiator=row.initiator, count=row.count)
        for row in education_engagement_initiators
    ]

    average_course_stmt = (
        sa.select(sa.func.avg(EducationInternship.course))
        .select_from(EducationInternshipMember)
        .join(EducationInternship, EducationInternship.id == EducationInternshipMember.internship_id)
        .where(
            EducationInternship.user_id == user_id,
            EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
            EducationInternship.course.is_not(None),
        )
    )
    average_participant_course = db.scalar(average_course_stmt)
    average_participant_course = (
        round(float(average_participant_course), 2) if average_participant_course is not None else None
    )

    return EducationStatsResponse(
        internships=InternshipStatusOverview(active=active, planned=planned, completed=completed),
        participants_total=participants_total,
        participants_by_status=participants_by_status,
        partner_companies=partner_companies,
        capacity_utilization=capacity_utilization,
        average_recruitment_days=average_recruitment_days,
        invite_activity=InviteActivity(
            active=codes_row.active or 0,
            used=codes_row.used or 0,
            expired=codes_row.expired or 0,
        ),
        engagement_status_breakdown=engagement_status_breakdown,
        engagement_initiator_breakdown=engagement_initiator_breakdown,
        average_participant_course=average_participant_course,
        published_internships=published_internships,
    )


def get_admin_stats(db: Session) -> AdminStatsResponse:
    active_applicants_stmt = (
        sa.select(sa.func.count())
        .select_from(User)
        .where(User.role == UserRole.APPLICANT, User.is_active.is_(True))
    )
    active_companies_stmt = (
        sa.select(sa.func.count())
        .select_from(User)
        .where(User.role == UserRole.COMPANY, User.is_active.is_(True))
    )
    active_educations_stmt = (
        sa.select(sa.func.count())
        .select_from(User)
        .where(User.role == UserRole.EDUCATION, User.is_active.is_(True))
    )

    active_applicants = db.scalar(active_applicants_stmt) or 0
    active_companies = db.scalar(active_companies_stmt) or 0
    active_educations = db.scalar(active_educations_stmt) or 0

    current_date = _current_date()
    active_internships_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternship)
        .where(
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
            EducationInternship.start_date <= current_date,
            EducationInternship.end_date >= current_date,
        )
    )
    active_internships = db.scalar(active_internships_stmt) or 0

    application_counts_stmt = (
        sa.select(
            sa.func.count().label("total"),
            sa.func.count(sa.case((VacancyApplication.status == VacancyApplicationStatus.APPROVED, 1))).label("approved"),
        )
        .select_from(VacancyApplication)
    )
    application_counts = db.execute(application_counts_stmt).one()
    employment_rate = _safe_div(application_counts.approved or 0, application_counts.total or 0)

    internship_duration_stmt = (
        sa.select(sa.func.avg(EducationInternship.end_date - EducationInternship.start_date))
        .select_from(EducationInternship)
        .where(EducationInternship.status == EducationInternshipStatus.PUBLISHED)
    )
    avg_internship_duration = _interval_to_days(db.scalar(internship_duration_stmt))

    now = _now_utc()
    current_period_start = now - timedelta(days=365)
    previous_period_start = now - timedelta(days=730)

    company_current_stmt = (
        sa.select(sa.func.count())
        .select_from(User)
        .where(
            User.role == UserRole.COMPANY,
            User.created_at >= current_period_start,
        )
    )
    company_previous_stmt = (
        sa.select(sa.func.count())
        .select_from(User)
        .where(
            User.role == UserRole.COMPANY,
            User.created_at >= previous_period_start,
            User.created_at < current_period_start,
        )
    )
    current_count = db.scalar(company_current_stmt) or 0
    previous_count = db.scalar(company_previous_stmt) or 0
    if previous_count == 0:
        company_growth_percent = 100.0 if current_count > 0 else 0.0
    else:
        company_growth_percent = round(((current_count - previous_count) / previous_count) * 100, 2)

    months = _month_start_sequence(12)
    series_start = months[0]
    series_start_dt = datetime.combine(series_start, time.min, tzinfo=timezone.utc)

    def _build_series(model):
        month_expr = sa.func.date_trunc("month", model.created_at).label("month")
        stmt = (
            sa.select(month_expr, sa.func.count().label("count"))
            .where(model.created_at >= series_start_dt)
            .group_by(month_expr)
        )
        rows = db.execute(stmt).all()
        mapping = {row.month.date(): row.count for row in rows}
        return [
            TimeSeriesPoint(month=m, count=mapping.get(m, 0))
            for m in months
        ]

    internship_series = _build_series(EducationInternship)
    vacancy_series = _build_series(CompanyVacancy)

    capacity_stmt = (
        sa.select(sa.func.sum(EducationInternship.capacity))
        .where(EducationInternship.status == EducationInternshipStatus.PUBLISHED)
    )
    total_capacity = db.scalar(capacity_stmt) or 0
    approved_participants_stmt = (
        sa.select(sa.func.count())
        .select_from(EducationInternshipMember)
        .join(EducationInternship, EducationInternship.id == EducationInternshipMember.internship_id)
        .where(
            EducationInternship.status == EducationInternshipStatus.PUBLISHED,
            EducationInternshipMember.status == InternshipParticipantStatus.APPROVED,
        )
    )
    approved_participants_total = db.scalar(approved_participants_stmt) or 0
    average_internship_fill_rate = _safe_div(approved_participants_total, total_capacity) if total_capacity else 0.0

    published_vacancies_stmt = sa.select(sa.func.count()).select_from(CompanyVacancy).where(CompanyVacancy.status == VacancyStatus.PUBLISHED)
    published_vacancies_total = db.scalar(published_vacancies_stmt) or 0
    total_applications_stmt = sa.select(sa.func.count()).select_from(VacancyApplication)
    total_applications = db.scalar(total_applications_stmt) or 0
    application_per_vacancy_ratio = (
        round(total_applications / published_vacancies_total, 2)
        if published_vacancies_total
        else None
    )

    engagement_status_stmt = (
        sa.select(EducationInternshipEngagement.status, sa.func.count().label("count"))
        .select_from(EducationInternshipEngagement)
        .group_by(EducationInternshipEngagement.status)
    )
    engagement_status_rows = db.execute(engagement_status_stmt).all()
    engagement_status_breakdown = [
        EducationEngagementStatusCount(status=row.status, count=row.count)
        for row in engagement_status_rows
    ]

    invite_summary_stmt = (
        sa.select(
            sa.func.count(sa.case((
                sa.and_(
                    EducationInternshipCode.used_at.is_(None),
                    EducationInternshipCode.revoked_at.is_(None),
                    EducationInternshipCode.expires_at >= now,
                ),
                1,
            ))).label("active"),
            sa.func.count(sa.case((EducationInternshipCode.used_at.is_not(None), 1))).label("used"),
            sa.func.count(sa.case((
                sa.and_(
                    EducationInternshipCode.used_at.is_(None),
                    EducationInternshipCode.expires_at < now,
                ),
                1,
            ))).label("expired"),
        )
        .select_from(EducationInternshipCode)
    )
    invite_summary_row = db.execute(invite_summary_stmt).one()

    return AdminStatsResponse(
        active_applicants=active_applicants,
        active_companies=active_companies,
        active_educations=active_educations,
        active_internships=active_internships,
        employment_rate=employment_rate,
        average_internship_duration_days=avg_internship_duration,
        company_growth_percent=company_growth_percent,
        internship_series=internship_series,
        vacancy_series=vacancy_series,
        average_internship_fill_rate=average_internship_fill_rate,
        application_per_vacancy_ratio=application_per_vacancy_ratio,
        engagement_status_breakdown=engagement_status_breakdown,
        invite_summary=InviteSummary(
            active=invite_summary_row.active or 0,
            used=invite_summary_row.used or 0,
            expired=invite_summary_row.expired or 0,
        ),
    )
