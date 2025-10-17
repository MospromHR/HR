from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import sqlalchemy as sa

from api.deps import get_db

router = APIRouter()


@router.get("/")
async def ping(db: Session = Depends(get_db)):
    db.execute(sa.text("SELECT 1"))
    return {"ping": "pong"}

