from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Schedule, User
from app.schemas import ScheduleCreate, ScheduleResponse
from app.services.auth import get_current_user

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleResponse)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.frequency not in {"weekly", "monthly"}:
        raise HTTPException(status_code=422, detail="Frequency must be weekly or monthly")
    if len(payload.delivery_time) != 5:
        raise HTTPException(status_code=422, detail="Delivery time must use HH:MM format")
    schedule = Schedule(id=str(uuid4()), user_id=user.id, **payload.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("", response_model=list[ScheduleResponse])
def list_schedules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(db.query(Schedule).filter(Schedule.user_id == user.id).order_by(Schedule.created_at.desc()).all())
