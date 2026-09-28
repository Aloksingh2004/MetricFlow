import pandas as pd

from app.services.validation import clean_dataframe, validate_dataframe


def valid_frame():
    return pd.DataFrame(
        [
            {
                "order_id": "A-1",
                "order_date": "2026-09-10",
                "product_name": "Tee",
                "quantity": "2",
                "unit_price": "499.00",
                "status": "Paid",
            }
        ]
    )


def test_validation_normalizes_common_statuses():
    result = validate_dataframe(valid_frame())
    assert result.valid
    assert result.valid_rows == 1
    assert clean_dataframe(valid_frame()).iloc[0]["status"] == "completed"


def test_validation_requires_core_columns():
    result = validate_dataframe(pd.DataFrame([{"order_id": "A-1"}]))
    assert not result.valid
    assert "Missing required columns" in result.errors[0]


def test_cleaning_removes_duplicate_order_ids():
    frame = pd.concat([valid_frame(), valid_frame()], ignore_index=True)
    assert len(clean_dataframe(frame)) == 1

