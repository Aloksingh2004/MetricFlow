from dataclasses import dataclass, field

import pandas as pd


REQUIRED_COLUMNS = {
    "order_id",
    "order_date",
    "product_name",
    "quantity",
    "unit_price",
    "status",
}
STATUS_MAP = {
    "paid": "completed",
    "complete": "completed",
    "completed": "completed",
    "fulfilled": "completed",
    "shipped": "completed",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "refund": "refunded",
    "refunded": "refunded",
    "pending": "pending",
    "processing": "pending",
}
VALID_STATUSES = set(STATUS_MAP.values())


@dataclass
class ValidationResult:
    valid: bool
    row_count: int
    valid_rows: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    preview: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "row_count": self.row_count,
            "valid_rows": self.valid_rows,
            "errors": self.errors,
            "warnings": self.warnings,
            "preview": self.preview,
        }


def load_dataframe(path: str) -> pd.DataFrame:
    if path.lower().endswith(".csv"):
        return pd.read_csv(path)
    return pd.read_excel(path)


def normalized_columns(frame: pd.DataFrame) -> pd.DataFrame:
    copied = frame.copy()
    copied.columns = [str(column).strip().lower().replace(" ", "_") for column in copied.columns]
    return copied


def validate_dataframe(frame: pd.DataFrame) -> ValidationResult:
    frame = normalized_columns(frame)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        return ValidationResult(
            valid=False,
            row_count=len(frame),
            valid_rows=0,
            errors=[f"Missing required columns: {', '.join(sorted(missing))}"],
            preview=frame.head(10).fillna("").to_dict(orient="records"),
        )

    errors: list[str] = []
    warnings: list[str] = []
    required_blank = frame[list(REQUIRED_COLUMNS)].isna().any(axis=1)
    if required_blank.any():
        errors.append(f"{required_blank.sum()} rows have missing required values.")

    dates = pd.to_datetime(frame["order_date"], errors="coerce")
    invalid_dates = dates.isna()
    if invalid_dates.any():
        errors.append(f"{invalid_dates.sum()} rows have invalid order dates.")

    quantity = pd.to_numeric(frame["quantity"], errors="coerce")
    invalid_quantity = quantity.isna() | (quantity <= 0)
    if invalid_quantity.any():
        errors.append(f"{invalid_quantity.sum()} rows have invalid quantities.")

    price = pd.to_numeric(frame["unit_price"], errors="coerce")
    invalid_price = price.isna() | (price < 0)
    if invalid_price.any():
        errors.append(f"{invalid_price.sum()} rows have invalid unit prices.")

    duplicates = frame.duplicated(subset=["order_id"], keep=False)
    if duplicates.any():
        warnings.append(f"{duplicates.sum()} duplicate order IDs detected; duplicates are skipped on import.")

    normal_statuses = frame["status"].astype(str).str.strip().str.lower().map(STATUS_MAP)
    unknown_statuses = normal_statuses.isna()
    if unknown_statuses.any():
        unknown = sorted(frame.loc[unknown_statuses, "status"].astype(str).unique())[:5]
        errors.append(f"Unknown order status values: {', '.join(unknown)}.")

    row_errors = required_blank | invalid_dates | invalid_quantity | invalid_price | unknown_statuses
    return ValidationResult(
        valid=not errors,
        row_count=len(frame),
        valid_rows=int((~row_errors).sum()),
        errors=errors,
        warnings=warnings,
        preview=frame.head(10).fillna("").to_dict(orient="records"),
    )


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    frame = normalized_columns(frame)
    frame = frame.copy()
    frame["order_date"] = pd.to_datetime(frame["order_date"], errors="coerce")
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")
    frame["unit_price"] = pd.to_numeric(frame["unit_price"], errors="coerce")
    frame["status"] = frame["status"].astype(str).str.strip().str.lower().map(STATUS_MAP)
    frame["order_id"] = frame["order_id"].astype(str).str.strip()
    frame["product_name"] = frame["product_name"].astype(str).str.strip()
    valid = (
        frame["order_id"].ne("")
        & frame["product_name"].ne("")
        & frame["order_date"].notna()
        & frame["quantity"].notna()
        & (frame["quantity"] > 0)
        & frame["unit_price"].notna()
        & (frame["unit_price"] >= 0)
        & frame["status"].isin(VALID_STATUSES)
    )
    cleaned = frame.loc[valid].drop_duplicates(subset=["order_id"], keep="first").copy()
    for optional in ("customer_id", "product_id", "payment_method"):
        if optional not in cleaned:
            cleaned[optional] = None
    return cleaned

