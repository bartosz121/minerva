import secrets
from datetime import datetime, timedelta, timezone


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def generate_token_expiration_date(duration: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=int(duration))
