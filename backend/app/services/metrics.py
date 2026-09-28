from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Order

SUCCESSFUL_STATUSES = {"completed"}


def _orders_in_range(db: Session, user_id: str, start: date | None, end: date | None) -> list[Order]:
    statement = select(Order).where(Order.user_id == user_id)
    if start:
        statement = statement.where(Order.order_date >= datetime.combine(start, datetime.min.time()))
    if end:
        statement = statement.where(Order.order_date < datetime.combine(end + timedelta(days=1), datetime.min.time()))
    return list(db.scalars(statement))


def get_summary(db: Session, user_id: str, start: date | None = None, end: date | None = None) -> dict:
    orders = _orders_in_range(db, user_id, start, end)
    revenue = _revenue(orders)
    order_count = len(orders)
    refunds = len([order for order in orders if order.status == "refunded"])
    return {
        "revenue": round(revenue, 2),
        "orders": order_count,
        "average_order_value": round(revenue / order_count, 2) if order_count else 0,
        "refund_rate": round(refunds / len(orders) * 100, 2) if orders else 0,
        "refunded_orders": refunds,
        "total_records": len(orders),
        "week_over_week_change": _weekly_change(db, user_id, start, end, revenue),
    }


def _weekly_change(db: Session, user_id: str, start: date | None, end: date | None, revenue: float) -> float:
    if not start or not end:
        return 0
    days = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    previous = _revenue(_orders_in_range(db, user_id, previous_start, previous_end))
    return round(((revenue - previous) / previous) * 100, 2) if previous else 0


def _revenue(orders: list[Order]) -> float:
    return sum(order.quantity * order.unit_price for order in orders if order.status in SUCCESSFUL_STATUSES)


def get_trends(db: Session, user_id: str, start: date | None = None, end: date | None = None) -> list[dict]:
    totals = defaultdict(float)
    for order in _orders_in_range(db, user_id, start, end):
        if order.status in SUCCESSFUL_STATUSES:
            totals[order.order_date.date().isoformat()] += order.quantity * order.unit_price
    return [{"date": day, "revenue": round(totals[day], 2)} for day in sorted(totals)]


def get_top_products(db: Session, user_id: str, start: date | None = None, end: date | None = None) -> list[dict]:
    products = defaultdict(lambda: {"revenue": 0.0, "quantity": 0})
    for order in _orders_in_range(db, user_id, start, end):
        if order.status in SUCCESSFUL_STATUSES:
            products[order.product_name]["revenue"] += order.quantity * order.unit_price
            products[order.product_name]["quantity"] += order.quantity
    ranked = sorted(products.items(), key=lambda item: item[1]["revenue"], reverse=True)[:10]
    return [
        {"product_name": name, "revenue": round(values["revenue"], 2), "quantity": values["quantity"]}
        for name, values in ranked
    ]


def get_status_breakdown(db: Session, user_id: str, start: date | None = None, end: date | None = None) -> list[dict]:
    counts = defaultdict(int)
    for order in _orders_in_range(db, user_id, start, end):
        counts[order.status] += 1
    return [{"status": status, "count": count} for status, count in sorted(counts.items())]
