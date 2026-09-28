from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models import Upload
from app.schemas import UploadResponse
from app.services.ingestion import import_orders
from app.services.validation import load_dataframe, validate_dataframe

router = APIRouter(prefix="/uploads", tags=["uploads"])
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _get_upload(db: Session, upload_id: str) -> Upload:
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.post("", response_model=UploadResponse)
async def create_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or "untitled"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Upload a CSV, XLS, or XLSX file")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    upload_id = str(uuid4())
    path = settings.upload_dir / f"{upload_id}{suffix}"
    path.write_bytes(await file.read())
    upload = Upload(id=upload_id, filename=filename, path=str(path))
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


@router.get("/{upload_id}", response_model=UploadResponse)
def get_upload(upload_id: str, db: Session = Depends(get_db)):
    return _get_upload(db, upload_id)


@router.post("/{upload_id}/validate")
def validate_upload(upload_id: str, db: Session = Depends(get_db)):
    upload = _get_upload(db, upload_id)
    try:
        result = validate_dataframe(load_dataframe(upload.path))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not read file: {error}") from error
    upload.row_count = result.row_count
    upload.status = "validated" if result.valid else "validation_failed"
    db.commit()
    return result.as_dict()


@router.post("/{upload_id}/import", response_model=UploadResponse)
def import_upload(upload_id: str, db: Session = Depends(get_db)):
    upload = _get_upload(db, upload_id)
    result = validate_dataframe(load_dataframe(upload.path))
    if not result.valid:
        raise HTTPException(status_code=422, detail={"message": "Fix validation errors before import", **result.as_dict()})
    upload.imported_rows = import_orders(db, upload.path, upload.id)
    upload.row_count = result.row_count
    upload.status = "imported"
    db.commit()
    db.refresh(upload)
    return upload

