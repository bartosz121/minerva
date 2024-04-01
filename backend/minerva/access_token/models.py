from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from minerva import utils
from minerva.access_token.utils import generate_token, generate_token_expiration_date
from minerva.core.config import settings
from minerva.core.db import Base
from minerva.core.db import mixins as db_mixins


def generate_token_expiration_date_default():
    return generate_token_expiration_date(settings.ACCESS_TOKEN_DURATION)


if TYPE_CHECKING:
    from minerva.users.models import User


class AccessToken(Base, db_mixins.TimestampMixin):
    __tablename__ = "access_tokens"

    token: Mapped[str] = mapped_column(String(1024), primary_key=True, default=generate_token)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    expiration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=generate_token_expiration_date_default
    )

    user: Mapped["User"] = relationship("User", lazy="selectin")

    @hybrid_property
    def expiration_date_int_from_now(self) -> int:
        return int((self.expiration_date - utils.datetime_now_utc()).total_seconds())
