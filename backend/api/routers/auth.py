from datetime import timedelta

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_config, get_db
from api.security import create_access_token, hash_password, verify_password
from config import Config
from database.schema.base import User

from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from ..schemas.user import UserResponse


router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    stmt = sa.select(User).where(User.email == payload.email)
    existing = db.scalar(stmt)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    cfg: Config = Depends(get_config),
) -> TokenResponse:
    stmt = sa.select(User).where(User.email == payload.email)
    user = db.scalar(stmt)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    expires_delta = timedelta(minutes=cfg.security.access_token_expire_minutes)
    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
            "is_superuser": user.is_superuser,
        },
        secret=cfg.security.jwt_secret,
        expires_delta=expires_delta,
    )
    return TokenResponse(access_token=token)
