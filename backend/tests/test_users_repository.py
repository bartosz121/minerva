from faker import Faker

from minerva.users.repository import UserRepository
from tests._factories import UserFactory

fake = Faker()


async def test_get_one_or_none_by_email_email(user_factory: UserFactory, user_repository: UserRepository):
    user = await user_factory.create()

    repo_user = await user_repository.get_one_or_none_by_email(user.email)
    assert repo_user
    assert repo_user.email == user.email


async def test_get_one_or_none_by_email_none(user_repository: UserRepository):
    repo_user = await user_repository.get_one_or_none_by_email(fake.email())
    assert repo_user is None
