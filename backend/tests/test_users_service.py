import pytest
from faker import Faker

from minerva.users.exceptions import EmailAlreadyExistsError
from minerva.users.schemas import UserSignUpIn
from minerva.users.security import verify_password
from minerva.users.service import UserService
from tests._factories import UserFactory

fake = Faker()


async def test_get_one_or_none_by_email(user_factory: UserFactory, user_service: UserService):
    user = await user_factory.create()

    service_user = await user_service.get_one_or_none_by_email(user.email)
    assert service_user
    assert service_user.email == user.email


async def test_get_one_or_none_by_email_none(user_service: UserService):
    service_user = await user_service.get_one_or_none_by_email(fake.email())
    assert service_user is None


async def test_create_from_schema(user_service: UserService):
    password = "password123!@#"  # noqa: S105
    schema = UserSignUpIn(email=fake.email(), password=password)

    user = await user_service.create_from_schema(schema)
    assert user.email == schema.email
    assert verify_password(password, user.hashed_password)


async def test_create_from_schema_raises_email_already_exists_error(
    user_factory: UserFactory, user_service: UserService
):
    user = await user_factory.create()

    schema = UserSignUpIn(email=user.email, password="password123!@#")  # noqa: S106

    with pytest.raises(EmailAlreadyExistsError):
        await user_service.create_from_schema(schema)
