from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models import Report
from app.schemas import ReportResponse
from app.services.report_generator import generate_weekly_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
def generate_report(start: date | None = None, end: date | None = None, db: Session = Depends(get_db)):
    report_id, path = generate_weekly_report(db, start, end)
    report = Report(id=report_id, filename=path.name, path=str(path))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report or not Path(report.path).is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.path, filename=report.filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

