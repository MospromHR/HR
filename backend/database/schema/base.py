from dataclasses import dataclass
import enum
from datetime import date, datetime
from uuid import UUID as UUID_t, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime


naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s__%(column_0_name)s",
    "ck": "ck_%(table_name)s__%(constraint_name)s",
    "fk": "fk_%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = sa.MetaData(naming_convention=naming_convention)


class UserRole(enum.StrEnum):
    APPLICANT = "applicant"
    COMPANY = "company"
    EDUCATION = "education"
    ADMIN = "admin"


@dataclass
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(sa.Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


@dataclass
class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    first_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    middle_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contacts: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


@dataclass
class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    company_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contacts: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


class VacancyStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


@dataclass
class CompanyVacancy(Base):
    __tablename__ = "company_vacancies"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vacancy_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    speciality: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    responsibilities: Mapped[str] = mapped_column(sa.Text, nullable=False)
    requirements: Mapped[str] = mapped_column(sa.Text, nullable=False)
    terms: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    work_schedule: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    work_place: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    map_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    probation: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    salary: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    additionally: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    task: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[VacancyStatus] = mapped_column(
        sa.Enum(VacancyStatus, name="vacancy_status"), nullable=False, default=VacancyStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


@dataclass
class EducationProfile(Base):
    __tablename__ = "education_profiles"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    organization_name: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    contacts: Mapped[dict[str, str] | None] = mapped_column(JSONB, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(sa.String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


class InternshipParticipantStatus(enum.StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"


class EducationInternshipStatus(enum.StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass
class EducationInternship(Base):
    __tablename__ = "education_internships"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    speciality_code: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    end_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    capacity: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    type: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    course: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    status: Mapped[EducationInternshipStatus] = mapped_column(
        sa.Enum(EducationInternshipStatus, name="education_internship_status"),
        nullable=False,
        default=EducationInternshipStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )


@dataclass
class EducationInternshipCode(Base):
    __tablename__ = "education_internship_codes"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    internship_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("education_internships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(sa.String(32), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by_user_id: Mapped[UUID_t | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


@dataclass
class EducationInternshipMember(Base):
    __tablename__ = "education_internship_members"

    id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    internship_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("education_internships.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID_t] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[InternshipParticipantStatus] = mapped_column(
        sa.Enum(InternshipParticipantStatus, name="internship_participant_status"),
        nullable=False,
        default=InternshipParticipantStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False
    )

    __table_args__ = (
        sa.UniqueConstraint("internship_id", "user_id", name="uq_internship_member"),
    )
