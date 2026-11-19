from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.config import get_settings
from app.dependencies import CurrentUser, DbSession
from app.models import User
from app.schemas import TokenRead, UserRead
from app.security import create_access_token, dummy_password_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["登录认证"])


@router.post("/login", response_model=TokenRead, summary="登录并获取 JWT Token")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = db.scalar(select(User).where(User.username == form.username))
    valid_password = verify_password(
        form.password, user.password_hash if user else dummy_password_hash
    )
    if not user or not valid_password or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenRead(
        access_token=create_access_token(user.id),
        expires_in=get_settings().access_token_expire_minutes * 60,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead, summary="获取当前登录用户")
def me(user: CurrentUser):
    return user
