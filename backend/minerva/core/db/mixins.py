from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


def datetime_now_utc() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime_now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime_now_utc, onupdate=datetime_now_utc
    )
