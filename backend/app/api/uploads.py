from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import get_db
from app.models import Upload, User
from app.schemas import UploadResponse
from app.services.auth import get_current_user
from app.services.ingestion import import_orders
from app.services.validation import load_dataframe, validate_dataframe

router = APIRouter(prefix="/uploads", tags=["uploads"])
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _get_upload(db: Session, upload_id: str, user: User) -> Upload:
    upload = db.query(Upload).filter(Upload.id == upload_id, Upload.user_id == user.id).one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.post("", response_model=UploadResponse)
async def create_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filename = file.filename or "untitled"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Upload a CSV, XLS, or XLSX file")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    upload_id = str(uuid4())
    path = settings.upload_dir / f"{upload_id}{suffix}"
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit")
    path.write_bytes(content)
    upload = Upload(id=upload_id, user_id=user.id, filename=filename, path=str(path))
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


@router.get("/{upload_id}", response_model=UploadResponse)
def get_upload(upload_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_upload(db, upload_id, user)


@router.post("/{upload_id}/validate")
def validate_upload(upload_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    upload = _get_upload(db, upload_id, user)
    try:
        result = validate_dataframe(load_dataframe(upload.path))
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Could not read file: {error}") from error
    upload.row_count = result.row_count
    upload.status = "validated" if result.valid else "validation_failed"
    db.commit()
    return result.as_dict()


@router.post("/{upload_id}/import", response_model=UploadResponse)
def import_upload(upload_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    upload = _get_upload(db, upload_id, user)
    result = validate_dataframe(load_dataframe(upload.path))
    if not result.valid:
        raise HTTPException(status_code=422, detail={"message": "Fix validation errors before import", **result.as_dict()})
    upload.imported_rows = import_orders(db, upload.path, upload.id, user.id)
    upload.row_count = result.row_count
    upload.status = "imported"
    db.commit()
    db.refresh(upload)
    return upload
