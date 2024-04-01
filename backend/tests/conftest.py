# ruff: noqa: ARG001
import asyncio
from secrets import token_urlsafe
from unittest import mock

import httpx
import pytest
from faker import Faker
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from minerva.access_token.models import AccessToken  # noqa: F401
from minerva.access_token.repository import AccessTokenRepository
from minerva.access_token.service import AccessTokenService
from minerva.core.config import settings
from minerva.core.db.dependencies import get_session as app_deps_get_session
from minerva.core.db.engine import Base
from minerva.core.repository.sqlalchemy import SQLAlchemyRepository
from minerva.main import app
from minerva.users.models import User  # noqa: F401
from minerva.users.repository import UserRepository
from minerva.users.security import get_password_hash
from minerva.users.service import UserService
from tests import _factories
from tests._database import Session, SessionSync, init_test_database
from tests._utils import Base as BaseTests
from tests._utils import TodoItem, TodoItemRepository, TodoItemService

DUMMY_COUNT = 100

AnyMock = mock.MagicMock | mock.AsyncMock


@pytest.fixture(scope="function")
def faker():
    return Faker()


@pytest.fixture(scope="function", autouse=True)
async def db():
    with init_test_database():
        db_uri = str(settings.DB_URI)
        db_uri_sync = str(settings.DB_URI_SYNC)
        engine = create_async_engine(db_uri, echo=False)
        engine_sync = create_engine(db_uri_sync, echo=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.run_sync(BaseTests.metadata.create_all)

        Session.configure(bind=engine)
        SessionSync.configure(bind=engine_sync)

        try:
            yield
        finally:
            await engine.dispose()
            engine_sync.dispose()


@pytest.fixture(scope="function")
async def session(db):
    session = Session()
    session.begin_nested()
    yield session
    await session.rollback()


@pytest.fixture(scope="function")
def session_sync(db):
    session = SessionSync()
    session.begin_nested()
    yield session
    session.rollback()


@pytest.fixture(scope="function")
async def insert_dummy(session: AsyncSession):
    from random import randint

    items = [
        TodoItem(title=f"Item {i}", description=f"{i}", is_completed=bool(randint(0, 1)))  # noqa: S311
        for i in range(DUMMY_COUNT)
    ]
    session.add_all(items)
    await session.commit()
    yield items
    for item in items:
        await session.delete(item)
    await session.commit()


@pytest.fixture
def sqlalchemy_repository_mock() -> SQLAlchemyRepository:
    class Repository_(SQLAlchemyRepository[mock.MagicMock, int]):  # noqa: N801
        model = mock.MagicMock

    return Repository_(
        session=mock.AsyncMock(spec=AsyncSession, bind=mock.MagicMock()),
        statement=mock.MagicMock(),
    )


@pytest.fixture(scope="function")
async def client(session):
    assert settings.ENVIRONMENT.is_testing

    app.dependency_overrides[app_deps_get_session] = lambda: session

    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(session, faker, access_token_factory, client: httpx.AsyncClient):
    password = "Password123!@#"  # noqa: S105
    access_token = await access_token_factory.create(
        user=User(email=faker.email(), hashed_password=get_password_hash(password))
    )

    response = await client.post("/users/sign-in", json={"email": access_token.user.email, "password": password})
    assert response.status_code == status.HTTP_200_OK

    setattr(client, "_access_token", access_token)  # noqa: B010

    yield client


@pytest.fixture(scope="function")
async def todo_item_repository(session: AsyncSession) -> TodoItemRepository:
    return TodoItemRepository(session)


@pytest.fixture(scope="function")
async def todo_item_service(todo_item_repository: TodoItemRepository) -> TodoItemService:
    return TodoItemService(todo_item_repository)


@pytest.fixture(scope="function")
async def user_repository(session: AsyncSession) -> UserRepository:
    return UserRepository(session)


@pytest.fixture(scope="function")
async def user_service(user_repository) -> UserService:
    return UserService(user_repository)


@pytest.fixture(scope="function")
async def access_token_repository(session: AsyncSession) -> AccessTokenRepository:
    return AccessTokenRepository(session)


@pytest.fixture(scope="function")
async def access_token_service(access_token_repository) -> AccessTokenService:
    return AccessTokenService(access_token_repository)


@pytest.fixture
async def user_factory() -> type[_factories.UserFactory]:
    return _factories.UserFactory


@pytest.fixture
async def access_token_factory() -> type[_factories.AccessTokenFactory]:
    return _factories.AccessTokenFactory
