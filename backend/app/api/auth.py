from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import User
from app.services.auth import authenticate_user, create_access_token, get_current_user
from app.services.login_limiter import clear_login_attempts, enforce_login_rate_limit, record_failed_login

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict[str, str]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    attempt_key = enforce_login_rate_limit(request, payload.email)
    user = authenticate_user(db, payload.email, payload.password)
    if not user or not user.is_active:
        record_failed_login(attempt_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    clear_login_attempts(attempt_key)
    access_token, expires_in = create_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {"email": user.email, "role": user.role},
    }


@router.get("/me")
def current_user(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}
