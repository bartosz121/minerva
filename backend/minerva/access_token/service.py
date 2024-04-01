from minerva import utils
from minerva.access_token import exceptions, models
from minerva.access_token.repository import AccessTokenRepository
from minerva.core.service import Service


class AccessTokenService(Service[models.AccessToken, str]):
    def __init__(self, repository: AccessTokenRepository) -> None:
        """AccessTokenService"""
        self.repository = repository

    async def validate_access_token(self, access_token: str) -> models.AccessToken:
        if access_token is None:
            raise exceptions.InvalidAccessTokenError()

        db_token = await self.repository.get_one_or_none(id=access_token)

        if db_token is None:
            raise exceptions.InvalidAccessTokenError()

        if db_token.expiration_date <= utils.datetime_now_utc():
            raise exceptions.ExpiredAccessTokenError()

        return db_token
