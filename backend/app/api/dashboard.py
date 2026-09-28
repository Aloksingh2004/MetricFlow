from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import User
from app.services.auth import get_current_user
from app.services.metrics import get_status_breakdown, get_summary, get_top_products, get_trends

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(start: date | None = None, end: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_summary(db, user.id, start, end)


@router.get("/trends")
def trends(start: date | None = None, end: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_trends(db, user.id, start, end)


@router.get("/top-products")
def top_products(start: date | None = None, end: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_top_products(db, user.id, start, end)


@router.get("/status-breakdown")
def status_breakdown(start: date | None = None, end: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return get_status_breakdown(db, user.id, start, end)
