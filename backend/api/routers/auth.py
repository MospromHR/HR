from datetime import timedelta
from typing import Any
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_config, get_db
from fastapi.security import OAuth2PasswordRequestForm

from api.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from config import Config
from database.schema.base import (
    ApplicantProfile,
    CompanyProfile,
    EducationProfile,
    User,
    UserRole,
)

from ..schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
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

    profile_model_map: dict[UserRole, type[ApplicantProfile | CompanyProfile | EducationProfile]] = {
        UserRole.APPLICANT: ApplicantProfile,
        UserRole.COMPANY: CompanyProfile,
        UserRole.EDUCATION: EducationProfile,
    }

    profile_model = profile_model_map.get(user.role)
    if profile_model is not None:
        db.add(profile_model(user_id=user.id))

    db.commit()
    db.refresh(user)
    return user


def _authenticate_user(db: Session, email: str, password: str) -> User:
    stmt = sa.select(User).where(User.email == email)
    user = db.scalar(stmt)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def _create_token_response(user: User, cfg: Config) -> TokenResponse:
    access_expires = timedelta(minutes=cfg.security.access_token_expire_minutes)
    refresh_expires = timedelta(minutes=cfg.security.refresh_token_expire_minutes)

    base_payload: dict[str, Any] = {"sub": str(user.id)}
    access_payload = {
        **base_payload,
        "role": str(user.role),
        "is_superuser": user.is_superuser,
    }

    access_token = create_access_token(
        access_payload,
        secret=cfg.security.jwt_secret,
        expires_delta=access_expires,
    )
    refresh_token = create_refresh_token(
        base_payload,
        secret=cfg.security.jwt_secret,
        expires_delta=refresh_expires,
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    cfg: Config = Depends(get_config),
) -> TokenResponse:
    user = _authenticate_user(db, payload.email, payload.password)
    return _create_token_response(user, cfg)


@router.post("/token", response_model=TokenResponse)
async def oauth2_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    cfg: Config = Depends(get_config),
) -> TokenResponse:
    user = _authenticate_user(db, form_data.username, form_data.password)
    return _create_token_response(user, cfg)


@router.post("/token/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    cfg: Config = Depends(get_config),
) -> TokenResponse:
    try:
        token_payload = decode_refresh_token(payload.refresh_token, secret=cfg.security.jwt_secret)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    sub = token_payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user_id = UUID(str(sub))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid subject") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return _create_token_response(user, cfg)
