from fastapi import Request
from ss.postgres import PostgresProvider

from config import Config


class Container:
    def __init__(self, db: PostgresProvider, config: Config):
        self.db = db
        self.config = config

    def dispose(self) -> None:
        self.db.dispose()


async def get_container(request: Request) -> "Container":
    return request.app.state.container
