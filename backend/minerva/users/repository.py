from uuid import UUID

from minerva.core.repository.sqlalchemy import SQLAlchemyRepository, sql_error_handler
from minerva.users.models import User


class UserRepository(SQLAlchemyRepository[User, UUID]):
    model = User

    async def get_one_or_none_by_email(self, email: str) -> User | None:
        stmt = self.statement.where(User.email == email)

        async with sql_error_handler():
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
