from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    if payload.email != settings.demo_email or payload.password != settings.demo_password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": "demo-access-token", "token_type": "bearer", "user": {"email": payload.email}}

