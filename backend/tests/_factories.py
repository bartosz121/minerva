import factory
from async_factory_boy.factory.sqlalchemy import AsyncSQLAlchemyFactory
from faker import Faker

from minerva.access_token.models import AccessToken
from minerva.users.models import User
from minerva.users.security import get_password_hash
from tests._database import Session

fake = Faker()


class BaseFactory(AsyncSQLAlchemyFactory):
    class Meta:  # type: ignore[misc]
        abstract = True
        sqlalchemy_session = Session
        sqlalchemy_session_persistence = "commit"


class UserFactory(BaseFactory):
    _default_password = "password123!@#"  # noqa: S105

    class Meta:  # type: ignore[misc]
        model = User

    email = factory.Faker("email")
    hashed_password = factory.LazyAttribute(lambda _: get_password_hash(UserFactory._default_password))


class AccessTokenFactory(BaseFactory):
    class Meta:  # type: ignore[misc]
        model = AccessToken

    user = factory.SubFactory(UserFactory)
