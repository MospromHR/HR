from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.orm import Session

from api.services import SimpleTTLCache
from config import Config

from .container import get_container


async def get_db(request: Request) -> AsyncIterator[Session]:
    container = await get_container(request)
    with container.db.get_db() as db:
        yield db


async def get_config(request: Request) -> Config:
    container = await get_container(request)
    return container.config


async def get_stats_cache(request: Request) -> SimpleTTLCache:
    container = await get_container(request)
    return container.analytics_cache
