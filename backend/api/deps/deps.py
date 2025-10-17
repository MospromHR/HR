from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.orm import Session


from .container import get_container


async def get_db(request: Request) -> AsyncIterator[Session]:
    container = await get_container(request)
    with container.db.get_db() as db:
        yield db
