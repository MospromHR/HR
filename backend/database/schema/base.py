from dataclasses import dataclass
from typing import List
import enum
from datetime import datetime
from uuid import UUID as UUID_t, uuid4

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import sqlalchemy as sa
from sqlalchemy.types import DateTime
from sqlalchemy.dialects.postgresql import UUID


naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s__%(column_0_name)s",
    "ck": "ck_%(table_name)s__%(constraint_name)s",
    "fk": "fk_%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = sa.MetaData(naming_convention=naming_convention)

@dataclass
class Example(Base):
    __tablename__ = "examples"
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    filed: Mapped[str] = mapped_column(nullable=False)
