from typing import Iterator
from contextlib import contextmanager

from sqlalchemy import URL, text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


class PostgresProvider():
    def __init__(
        self,
        *,
        username: str | None = None,
        password: str | None = None,
        host: str | None = None,
        port: int | None = None,
        database: str | None = None,
        debug: bool = True,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
        pool_use_lifo: bool = True,
    ):
        
        self.url = URL.create(
            "postgresql+psycopg",
            username=username,
            password=password,
            host=host,
            port=port,
            database=database,
        )
        
        self.engine: Engine = create_engine(
            self.url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
            pool_use_lifo=pool_use_lifo,
            echo=debug,
        )
        
        self.Session = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )
    
    def ping(self):
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    
    @contextmanager
    def get_db(self) -> Iterator[Session]:
        with self.Session() as db:
            try:
                yield db
                db.commit()
            except:
                db.rollback()
                raise
    
    def get_url(self) -> str:
        print(self.url)
        return self.url.render_as_string(hide_password=False)

    def dispose(self):
        self.engine.dispose()