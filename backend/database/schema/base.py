from dataclasses import dataclass
import enum
from datetime import datetime
from uuid import UUID as UUID_t, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
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
