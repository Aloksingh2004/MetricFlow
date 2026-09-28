from datetime import date
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.services.metrics import get_summary, get_top_products, get_trends


def generate_weekly_report(db: Session, start: date | None, end: date | None) -> tuple[str, Path]:
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    report_id = str(uuid4())
    file_path = settings.report_dir / f"weekly-report-{report_id}.xlsx"
    summary = get_summary(db, start, end)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        pd.DataFrame([summary]).to_excel(writer, sheet_name="Summary", index=False)
        pd.DataFrame(get_trends(db, start, end)).to_excel(writer, sheet_name="Revenue Trend", index=False)
        pd.DataFrame(get_top_products(db, start, end)).to_excel(writer, sheet_name="Top Products", index=False)
    return report_id, file_path

