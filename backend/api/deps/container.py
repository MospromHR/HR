from fastapi import Request
from ss.postgres import PostgresProvider

from api.services import SimpleTTLCache
from config import Config


class Container:
    def __init__(self, db: PostgresProvider, config: Config):
        self.db = db
        self.config = config
        self.analytics_cache = SimpleTTLCache(config.analytics.cache_ttl_seconds)

    def dispose(self) -> None:
        self.db.dispose()


async def get_container(request: Request) -> "Container":
    return request.app.state.container
