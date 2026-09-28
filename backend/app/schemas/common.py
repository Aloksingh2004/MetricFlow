from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: str
    row_count: int | None = None
    imported_rows: int = 0
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    report_type: str
    created_at: datetime


class ScheduleCreate(BaseModel):
    report_type: str = "weekly"
    frequency: str
    delivery_time: str


class ScheduleResponse(ScheduleCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    created_at: datetime
