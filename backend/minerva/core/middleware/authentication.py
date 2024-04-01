from fastapi.requests import HTTPConnection
from starlette.authentication import AuthCredentials, SimpleUser
from starlette.authentication import AuthenticationBackend as StarletteAuthenticationBackend

from minerva.access_token.models import AccessToken
from minerva.access_token.repository import AccessTokenRepository
from minerva.access_token.service import AccessTokenService
from minerva.core.config import settings
from minerva.core.db import main as db
from minerva.users.models import User


class AuthenticatedUser(SimpleUser):
    user: User
    access_token: AccessToken

    def __init__(self, access_token: AccessToken) -> None:
        super().__init__(access_token.user.email)
        self.user = access_token.user
        self.access_token = access_token


class AuthenticationBackend(StarletteAuthenticationBackend):
    def __init__(self) -> None:
        super().__init__()
        self.access_token_service = AccessTokenService(AccessTokenRepository(db.session()))

    async def authenticate(self, conn: HTTPConnection) -> tuple[AuthCredentials, AuthenticatedUser] | None:
        request_access_token = conn.headers.get("Authentication") or conn.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)

        if request_access_token is None:
            return None

        access_token = await self.access_token_service.validate_access_token(request_access_token)

        return AuthCredentials(["authenticated"]), AuthenticatedUser(access_token)
