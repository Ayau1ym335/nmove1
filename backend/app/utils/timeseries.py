from datetime import date, timedelta
from typing import Any

from app.schemas.trends import TrendDataPoint

def gap_fill_chart(
    raw_rows: list[Any],
    from_date: date,
    to_date: date,
) -> list[TrendDataPoint]:
    """
    Fills gaps in a sparse list of daily rows.
    raw_rows should be a list of objects or dicts with properties/keys equivalent to TrendDataPoint
    ('bucket' or 'date', 'value', 'session_count').
    """
    db_dict = {}
    for row in raw_rows:
        bucket_date = None
        
        # Support both object access and dict access depending on who calls it (Trend vs Doctor service)
        if hasattr(row, "bucket") and row.bucket:
            bucket_date = row.bucket.date() if hasattr(row.bucket, 'date') else row.bucket
        elif hasattr(row, "date") and row.date:
            bucket_date = row.date.date() if hasattr(row.date, 'date') else row.date
        elif isinstance(row, dict):
            bucket_val = row.get("bucket") or row.get("date")
            if bucket_val:
                bucket_date = bucket_val.date() if hasattr(bucket_val, "date") else bucket_val

        value = None
        if isinstance(row, dict):
            value = row.get("value")
        else:
            value = getattr(row, "value", None)

        session_count = 0
        if isinstance(row, dict):
            session_count = row.get("session_count", 0)
        else:
            session_count = getattr(row, "session_count", 0)

        if bucket_date:
            db_dict[bucket_date] = {
                "value": float(value) if value is not None else None,
                "session_count": int(session_count) if session_count is not None else 0
            }

    filled_data = []
    current_date = from_date
    while current_date <= to_date:
        if current_date in db_dict:
            filled_data.append(TrendDataPoint(
                date=current_date,
                value=db_dict[current_date]["value"],
                session_count=db_dict[current_date]["session_count"]
            ))
        else:
            filled_data.append(TrendDataPoint(
                date=current_date,
                value=None,
                session_count=0
            ))
        current_date += timedelta(days=1)

    return filled_data
