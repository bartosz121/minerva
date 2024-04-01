from typing import Annotated

from fastapi import Depends

from minerva.access_token.repository import AccessTokenRepository as AccessTokenRepository_
from minerva.access_token.service import AccessTokenService as AccessTokenService_
from minerva.core.db import dependencies as db_deps


def get_access_token_repository(session: db_deps.DbSession) -> AccessTokenRepository_:
    repository = AccessTokenRepository_(session)
    return repository


def get_access_token_service(repository: AccessTokenRepository_ = Depends(get_access_token_repository)):
    service = AccessTokenService_(repository)
    return service


AccessTokenRepository = Annotated[AccessTokenRepository_, Depends(get_access_token_repository)]
AccessTokenService = Annotated[AccessTokenService_, Depends(get_access_token_service)]
