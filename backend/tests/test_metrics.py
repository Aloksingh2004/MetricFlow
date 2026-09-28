from datetime import datetime

from app.models import Order
from app.services import metrics


def _order(order_id: str, status: str, quantity: int, unit_price: float) -> Order:
    return Order(
        user_id="user-1",
        order_id=order_id,
        order_date=datetime(2026, 9, 10),
        product_name="Tee",
        quantity=quantity,
        unit_price=unit_price,
        status=status,
    )


def test_summary_counts_all_valid_orders_but_revenue_only_completed(monkeypatch):
    orders = [
        _order("ORD-1", "completed", 2, 100.0),
        _order("ORD-2", "refunded", 1, 100.0),
        _order("ORD-3", "cancelled", 1, 100.0),
    ]
    monkeypatch.setattr(metrics, "_orders_in_range", lambda *_: orders)

    summary = metrics.get_summary(object(), "user-1")

    assert summary["revenue"] == 200.0
    assert summary["orders"] == 3
    assert summary["average_order_value"] == round(200 / 3, 2)
    assert summary["refund_rate"] == round(100 / 3, 2)
