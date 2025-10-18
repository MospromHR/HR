from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.deps import get_db

router = APIRouter()


@router.get("/")
async def ping(db: Session = Depends(get_db)):
    db.execute(sa.text("SELECT 1"))
    return {"ping": "pong"}


@router.get("/startup")
async def startup_time(request: Request):
    started_at = getattr(request.app.state, "startup_time", None)
    return {
        "startup_time": started_at.isoformat() if started_at else None,
        "rev": "1"
    }

