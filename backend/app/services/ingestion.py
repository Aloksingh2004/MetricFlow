from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order
from app.services.validation import clean_dataframe, load_dataframe


def import_orders(db: Session, file_path: str, upload_id: str) -> int:
    frame = clean_dataframe(load_dataframe(file_path))
    existing_ids = set(db.scalars(select(Order.order_id).where(Order.order_id.in_(frame["order_id"].tolist()))))
    imported = 0
    for record in frame.to_dict(orient="records"):
        if record["order_id"] in existing_ids:
            continue
        db.add(
            Order(
                order_id=record["order_id"],
                order_date=record["order_date"].to_pydatetime(),
                customer_id=_string_or_none(record.get("customer_id")),
                product_id=_string_or_none(record.get("product_id")),
                product_name=record["product_name"],
                quantity=int(record["quantity"]),
                unit_price=float(record["unit_price"]),
                status=record["status"],
                payment_method=_string_or_none(record.get("payment_method")),
                source_upload_id=upload_id,
            )
        )
        imported += 1
    db.commit()
    return imported


def _string_or_none(value):
    return None if value is None or str(value).lower() == "nan" else str(value).strip()

