from __future__ import annotations

import json
import logging
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

from faker import Faker
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from api.security import hash_password
from database.schema.base import (
    ApplicantProfile,
    CompanyProfile,
    CompanyVacancy,
    EducationInternship,
    EducationInternshipCode,
    EducationInternshipMember,
    EducationInternshipStatus,
    EducationProfile,
    InternshipParticipantStatus,
    User,
    UserRole,
    VacancyStatus,
)
from ss.postgres import PostgresProvider


logger = logging.getLogger(__name__)


class DemoApplicant(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    bio: str | None = None
    contacts: dict[str, str] | None = None
    avatar_url: str | None = None


class DemoCompany(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    company_name: str | None = None
    description: str | None = None
    contacts: dict[str, str] | None = None
    logo_url: str | None = None


class DemoEducation(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    organization_name: str | None = None
    description: str | None = None
    contacts: dict[str, str] | None = None
    logo_url: str | None = None


class DemoDataset(BaseModel):
    applicants: list[DemoApplicant] = Field(default_factory=list)
    companies: list[DemoCompany] = Field(default_factory=list)
    educations: list[DemoEducation] = Field(default_factory=list)


TARGET_APPLICANTS = 10
TARGET_COMPANIES = 10
TARGET_EDUCATIONS = 10
TARGET_VACANCIES = 12
TARGET_INTERNSHIPS = 10
CODES_PER_INTERNSHIP = 3
MEMBERS_PER_INTERNSHIP = 5
DEFAULT_RANDOM_PASSWORD = "demo12345"


def _read_demo_payload() -> DemoDataset:
    candidates = [
        Path.cwd() / "demo.json",
        Path(__file__).resolve().parent.parent / "demo.json",
    ]

    for path in candidates:
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                logger.info("Loaded demo accounts from %s", path)
                return DemoDataset.model_validate(payload)
            except json.JSONDecodeError as exc:
                logger.warning("Failed to parse demo accounts file %s: %s", path, exc)
                break

    logger.info("Demo accounts file not found, using defaults")
    return DemoDataset()


def _generate_contacts(faker: Faker) -> dict[str, str]:
    return {
        "email": faker.free_email(),
        "phone": faker.phone_number(),
        "telegram": f"@{faker.user_name()}",
    }


def _create_user(session: Session, *, email: str, password: str, role: UserRole) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    session.flush()
    return user


def _create_applicant(
    session: Session,
    faker: Faker,
    *,
    email: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
    middle_name: str | None = None,
    bio: str | None = None,
    contacts: dict[str, str] | None = None,
    avatar_url: str | None = None,
) -> User:
    user = _create_user(session, email=email, password=password, role=UserRole.APPLICANT)

    first_name = first_name or faker.first_name()
    last_name = last_name or faker.last_name()
    middle_name = middle_name or faker.first_name()
    bio = bio or "\n".join(faker.paragraphs(nb=2))
    contacts = contacts or _generate_contacts(faker)
    avatar_url = avatar_url or (
        "https://api.dicebear.com/7.x/initials/svg?seed="
        f"{quote_plus(first_name + last_name)}"
    )

    profile = ApplicantProfile(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        bio=bio,
        contacts=contacts,
        avatar_url=avatar_url,
    )
    session.add(profile)
    return user


def _create_company(
    session: Session,
    faker: Faker,
    *,
    email: str,
    password: str,
    company_name: str | None = None,
    description: str | None = None,
    contacts: dict[str, str] | None = None,
    logo_url: str | None = None,
) -> User:
    user = _create_user(session, email=email, password=password, role=UserRole.COMPANY)

    company_name = company_name or faker.company()
    description = description or "\n".join(faker.paragraphs(nb=2))
    contacts = contacts or _generate_contacts(faker)
    logo_url = logo_url or f"https://picsum.photos/seed/{quote_plus(company_name)}/200"

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        description=description,
        contacts=contacts,
        logo_url=logo_url,
    )
    session.add(profile)
    return user


def _create_education(
    session: Session,
    faker: Faker,
    *,
    email: str,
    password: str,
    organization_name: str | None = None,
    description: str | None = None,
    contacts: dict[str, str] | None = None,
    logo_url: str | None = None,
) -> User:
    user = _create_user(session, email=email, password=password, role=UserRole.EDUCATION)

    organization_name = organization_name or f"{faker.company()} колледж"
    description = description or "\n".join(faker.paragraphs(nb=2))
    contacts = contacts or _generate_contacts(faker)
    logo_url = logo_url or f"https://picsum.photos/seed/{quote_plus(organization_name)}/200"

    profile = EducationProfile(
        user_id=user.id,
        organization_name=organization_name,
        description=description,
        contacts=contacts,
        logo_url=logo_url,
    )
    session.add(profile)
    return user


def _generate_unique_email(faker: Faker, used: set[str]) -> str:
    while True:
        candidate = faker.free_email().lower()
        if candidate not in used:
            used.add(candidate)
            return candidate


def _create_vacancies(
    session: Session,
    faker: Faker,
    *,
    company_users: Iterable[User],
    target: int,
) -> None:
    company_users = list(company_users)
    if not company_users:
        logger.info("Skipping vacancy generation - no company users found")
        return

    city_cache: list[str] = []
    code_values: set[str] = set()

    for idx in range(target):
        company_user = company_users[idx % len(company_users)]
        vacancy_name = faker.job()
        speciality = faker.job()
        responsibilities = "\n".join(faker.paragraphs(nb=2))
        requirements = "\n".join(faker.paragraphs(nb=2))
        terms = "\n".join(faker.paragraphs(nb=1))
        work_schedule = random.choice([
            "Гибкий график",
            "Полный день",
            "Удаленная работа",
            "Сменный график",
        ])
        if len(city_cache) < len(company_users):
            city_cache.append(faker.city())
        work_place = city_cache[idx % len(city_cache)]
        map_url = f"https://maps.google.com/?q={quote_plus(faker.address().replace('\n', ', '))}"
        probation = random.choice(["1 месяц", "2 месяца", "3 месяца"])
        salary = f"от {faker.random_int(min=40000, max=160000):,} ₽".replace(",", " ")
        additionally = "\n".join(faker.paragraphs(nb=1))
        task = faker.paragraph()

        vacancy = CompanyVacancy(
            user_id=company_user.id,
            vacancy_name=vacancy_name,
            speciality=speciality,
            responsibilities=responsibilities,
            requirements=requirements,
            terms=terms,
            work_schedule=work_schedule,
            work_place=work_place,
            map_url=map_url,
            probation=probation,
            salary=salary,
            additionally=additionally,
            task=task,
            status=VacancyStatus.PUBLISHED,
        )
        session.add(vacancy)


def _create_internships(
    session: Session,
    faker: Faker,
    *,
    education_users: Iterable[User],
    applicant_users: list[User],
    target: int,
) -> None:
    education_users = list(education_users)
    if not education_users:
        logger.info("Skipping internship generation - no education users found")
        return

    if not applicant_users:
        logger.info("Skipping internship members - no applicant users found")

    def speciality_code() -> str:
        return f"{faker.random_int(10, 99)}.{faker.random_int(10, 99)}.{faker.random_int(100, 999)}"

    now = datetime.now(timezone.utc)
    internships: list[EducationInternship] = []
    for idx in range(target):
        education_user = education_users[idx % len(education_users)]
        start = date.today() + timedelta(days=faker.random_int(min=5, max=40))
        end = start + timedelta(days=faker.random_int(min=45, max=120))
        capacity = faker.random_int(min=10, max=40)

        internship = EducationInternship(
            user_id=education_user.id,
            title=f"Стажировка: {faker.catch_phrase()}",
            speciality_code=speciality_code(),
            start_date=start,
            end_date=end,
            capacity=capacity,
            status=EducationInternshipStatus.PUBLISHED,
        )
        session.add(internship)
        session.flush()
        internships.append(internship)

        for _ in range(CODES_PER_INTERNSHIP):
            code = faker.bothify(text="INT-####-????").upper()
            while code in code_values:
                code = faker.bothify(text="INT-####-????").upper()
            code_values.add(code)
            expires_at = now + timedelta(days=faker.random_int(min=15, max=60))
            code_row = EducationInternshipCode(
                internship_id=internship.id,
                code=code,
                expires_at=expires_at,
            )
            session.add(code_row)

    if not applicant_users:
        return

    for internship in internships:
        members = random.sample(
            applicant_users,
            k=min(len(applicant_users), MEMBERS_PER_INTERNSHIP),
        )
        for user in members:
            member = EducationInternshipMember(
                internship_id=internship.id,
                user_id=user.id,
                status=random.choice(
                    [
                        InternshipParticipantStatus.APPROVED,
                        InternshipParticipantStatus.PENDING,
                    ]
                ),
            )
            session.add(member)


def seed_demo_data(pg: PostgresProvider, *, reserved_emails: Iterable[str] | None = None) -> None:
    faker = Faker("ru_RU")
    faker.seed_instance(42)

    dataset = _read_demo_payload()
    used_emails: set[str] = set(email.lower() for email in (reserved_emails or []))

    with pg.get_db() as session:
        applicant_users: list[User] = []
        company_users: list[User] = []
        education_users: list[User] = []

        for entry in dataset.applicants:
            used_emails.add(entry.email.lower())
            applicant_users.append(
                _create_applicant(
                    session,
                    faker,
                    email=entry.email.lower(),
                    password=entry.password,
                    first_name=entry.first_name,
                    last_name=entry.last_name,
                    middle_name=entry.middle_name,
                    bio=entry.bio,
                    contacts=entry.contacts,
                    avatar_url=entry.avatar_url,
                )
            )

        for entry in dataset.companies:
            used_emails.add(entry.email.lower())
            company_users.append(
                _create_company(
                    session,
                    faker,
                    email=entry.email.lower(),
                    password=entry.password,
                    company_name=entry.company_name,
                    description=entry.description,
                    contacts=entry.contacts,
                    logo_url=entry.logo_url,
                )
            )

        for entry in dataset.educations:
            used_emails.add(entry.email.lower())
            education_users.append(
                _create_education(
                    session,
                    faker,
                    email=entry.email.lower(),
                    password=entry.password,
                    organization_name=entry.organization_name,
                    description=entry.description,
                    contacts=entry.contacts,
                    logo_url=entry.logo_url,
                )
            )

        while len(applicant_users) < TARGET_APPLICANTS:
            email = _generate_unique_email(faker, used_emails)
            applicant_users.append(
                _create_applicant(
                    session,
                    faker,
                    email=email,
                    password=DEFAULT_RANDOM_PASSWORD,
                )
            )

        while len(company_users) < TARGET_COMPANIES:
            email = _generate_unique_email(faker, used_emails)
            company_users.append(
                _create_company(
                    session,
                    faker,
                    email=email,
                    password=DEFAULT_RANDOM_PASSWORD,
                )
            )

        while len(education_users) < TARGET_EDUCATIONS:
            email = _generate_unique_email(faker, used_emails)
            education_users.append(
                _create_education(
                    session,
                    faker,
                    email=email,
                    password=DEFAULT_RANDOM_PASSWORD,
                )
            )

        _create_vacancies(session, faker, company_users=company_users, target=TARGET_VACANCIES)
        _create_internships(
            session,
            faker,
            education_users=education_users,
            applicant_users=applicant_users,
            target=TARGET_INTERNSHIPS,
        )

        logger.info(
            "Demo data generated: %s applicants, %s companies, %s educations",
            len(applicant_users),
            len(company_users),
            len(education_users),
        )
