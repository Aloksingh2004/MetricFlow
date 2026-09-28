from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.metrics import get_status_breakdown, get_summary, get_top_products, get_trends

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    return get_summary(db, start, end)


@router.get("/trends")
def trends(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    return get_trends(db, start, end)


@router.get("/top-products")
def top_products(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    return get_top_products(db, start, end)


@router.get("/status-breakdown")
def status_breakdown(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    return get_status_breakdown(db, start, end)

