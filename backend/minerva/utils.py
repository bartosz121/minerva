from datetime import datetime, timezone


def datetime_now_utc() -> datetime:
    return datetime.now(timezone.utc)
