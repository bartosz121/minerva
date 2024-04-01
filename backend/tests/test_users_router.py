from datetime import datetime, timedelta, timezone
from unittest import mock

import freezegun
from faker import Faker
from fastapi import status
from httpx import AsyncClient

from minerva.access_token.service import AccessTokenService
from minerva.core.config import settings
from minerva.users.schemas import SignInResponse, UserRead
from tests._factories import UserFactory

fake = Faker()

PASSWORD = "Password123!@#"  # noqa: S105


async def test_sign_up(client: AsyncClient):
    data = {"email": fake.email(), "password": PASSWORD}

    response = await client.post("/users/sign-up", json=data)
    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert response_data.keys() == UserRead.model_json_schema()["properties"].keys()
    assert response_data["id"]
    assert response_data["email"] == data["email"]


async def test_sign_up_checks_password_complexity(client: AsyncClient):
    data = {"email": fake.email(), "password": "abc123"}
    response = await client.post("/users/sign-up", json=data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_sign_up_raises_409_if_email_exists(user_factory: UserFactory, client: AsyncClient):
    user = await user_factory.create()
    data = {"email": user.email, "password": PASSWORD}

    response = await client.post("/users/sign-up", json=data)
    assert response.status_code == status.HTTP_409_CONFLICT


@freezegun.freeze_time(datetime(1969, 6, 16, 12, 0, 0, 0, tzinfo=timezone.utc))
async def test_sign_in(user_factory: UserFactory, client: AsyncClient):
    user = await user_factory.create()
    data = {"email": user.email, "password": UserFactory._default_password}

    response = await client.post("/users/sign-in", json=data)
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    assert response_data.keys() == SignInResponse.model_json_schema()["properties"].keys()

    assert client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    assert client.cookies[settings.ACCESS_TOKEN_COOKIE_NAME] == response_data["token"]

    expected_expiration_date = datetime.now() + timedelta(seconds=settings.ACCESS_TOKEN_DURATION)  # noqa: DTZ005
    assert datetime.strptime(response_data["expirationDate"], "%Y-%m-%dT%H:%M:%SZ") == expected_expiration_date  # noqa: DTZ007


async def test_sign_in_raises_400_if_email_doesnt_exist(client: AsyncClient):
    data = {"email": fake.email(), "password": PASSWORD}

    response = await client.post("/users/sign-in", json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_sign_in_raises_400_if_wrong_password(user_factory: UserFactory, client: AsyncClient):
    user = await user_factory.create()
    data = {"email": user.email, "password": "password123!@#123!@#"}

    response = await client.post("/users/sign-in", json=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@mock.patch.object(AccessTokenService, "validate_access_token")
async def test_sign_out(
    mock_validate_access_token: mock.MagicMock,
    authenticated_client: AsyncClient,
):
    access_token = getattr(authenticated_client, "_access_token")  # noqa: B009
    mock_validate_access_token.return_value = access_token

    response = await authenticated_client.get("/users/sign-out")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert authenticated_client.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME) is None


async def test_sign_out_raises_forbidden_if_not_authenticated(client: AsyncClient):
    response = await client.get("/users/sign-out")
    assert response.status_code == status.HTTP_403_FORBIDDEN
