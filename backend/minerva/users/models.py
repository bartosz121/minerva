from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from minerva.core.db import Base
from minerva.core.db import mixins as db_mixins


class User(Base, db_mixins.TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(default=uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(String(length=255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(length=2024))

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
