from contextlib import asynccontextmanager
from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.schema.base import Base
from ss.config import ConfigProvider
from ss.postgres import PostgresProvider

from config import Config
import logging
from api.deps import Container
from api.routers import system


logger = logging.getLogger("uvicorn.error")


def create_test_data(pg: PostgresProvider):
    with pg.get_db() as db:
        pass
        db.flush()
        db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = ConfigProvider(
        yaml_path=Path.cwd()/"config.yaml",
        env_path=Path.cwd()/".env"
    ).as_object(Config)
    logger.info(f"Result config loaded:\n{cfg.model_dump_json(indent=4)}")
    
    db = PostgresProvider(
        username=cfg.postgres.username,
        password=cfg.postgres.password,
        host=cfg.postgres.host,
        port=cfg.postgres.port,
        database=cfg.postgres.database,
        debug=True
    )
    db.ping()
    
    Base.metadata.drop_all(bind=db.engine)
    Base.metadata.create_all(bind=db.engine)
    
    create_test_data(db)
    
    
    container = Container(db)
    app.state.container = container
        
    yield
    
    container.dispose()


def create_app():
    root_path = os.getenv("APP_ROOT_PATH", "")
    app = FastAPI(lifespan=lifespan, root_path=root_path)
    app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app
    

app = create_app()
