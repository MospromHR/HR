from contextlib import asynccontextmanager
from pathlib import Path
import logging
import os

import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import Container
from api.routers import (
    admin,
    applicants,
    auth,
    companies,
    education_internships,
    educations,
    system,
    users,
)
from api.security import hash_password
from config import Config
from database.schema.base import Base, User, UserRole
from ss.config import ConfigProvider
from ss.postgres import PostgresProvider


logger = logging.getLogger("uvicorn.error")


def ensure_superuser(pg: PostgresProvider, cfg: Config) -> None:
    with pg.get_db() as db:
        role = UserRole(cfg.superuser.role)
        hashed_password = hash_password(cfg.superuser.password)

        stmt = sa.select(User).where(User.email == cfg.superuser.email)
        user = db.scalar(stmt)

        if user is None:
            user = User(
                email=cfg.superuser.email,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_superuser=True,
            )
            db.add(user)
        else:
            user.hashed_password = hashed_password
            user.role = role
            user.is_active = True
            user.is_superuser = True

        db.flush()
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = ConfigProvider(
        yaml_path=Path.cwd() / "config.yaml",
        env_path=Path.cwd() / ".env",
    ).as_object(Config)
    logger.info("Result config loaded:\n%s", cfg.model_dump_json(indent=4))

    db = PostgresProvider(
        username=cfg.postgres.username,
        password=cfg.postgres.password,
        host=cfg.postgres.host,
        port=cfg.postgres.port,
        database=cfg.postgres.database,
        debug=True,
    )
    db.ping()

    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)

    ensure_superuser(db, cfg)

    container = Container(db, cfg)
    app.state.container = container

    try:
        yield
    finally:
        container.dispose()


def create_app() -> FastAPI:
    root_path = os.getenv("APP_ROOT_PATH", "")
    app = FastAPI(lifespan=lifespan, root_path=root_path)
    app.include_router(system.router, prefix="/v1/system", tags=["System"])
    app.include_router(auth.router, prefix="/v1/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/v1", tags=["Users"])
    app.include_router(applicants.router, prefix="/v1")
    app.include_router(companies.router, prefix="/v1")
    app.include_router(educations.router, prefix="/v1")
    app.include_router(education_internships.router, prefix="/v1")
    app.include_router(admin.router, prefix="/v1")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()
