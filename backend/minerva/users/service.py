from minerva.core.service import Service
from minerva.users import models, schemas, security
from minerva.users.exceptions import EmailAlreadyExistsError
from minerva.users.repository import UserRepository


class UserService(Service[models.User, str]):
    def __init__(self, repository: UserRepository) -> None:
        """UserService"""
        self.repository = repository

    async def get_one_or_none_by_email(self, email: str) -> models.User | None:
        return await self.repository.get_one_or_none_by_email(email)

    async def create_from_schema(self, schema: schemas.UserSignUpIn) -> models.User:
        is_email_taken = await self.exists(email=schema.email)
        if is_email_taken:
            raise EmailAlreadyExistsError()

        hashed_password = security.get_password_hash(schema.password)
        user = models.User(email=schema.email, hashed_password=hashed_password)
        return await self.create(user)
