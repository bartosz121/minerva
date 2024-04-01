from typing import Annotated

from fastapi import Depends, HTTPException, Request

from minerva.core.db import dependencies as db_deps
from minerva.core.middleware.authentication import AuthenticatedUser
from minerva.users.repository import UserRepository as UserRepository_
from minerva.users.service import UserService as UserService_


def get_user_repository(session: db_deps.DbSession) -> UserRepository_:
    repository = UserRepository_(session)
    return repository


def get_user_service(repository: UserRepository_ = Depends(get_user_repository)) -> UserService_:
    service = UserService_(repository)
    return service


def get_auth_middleware_current_user(request: Request) -> AuthenticatedUser:
    user = request.user
    if not isinstance(user, AuthenticatedUser):
        raise HTTPException(status_code=403)
    return user


UserRepository = Annotated[UserRepository_, Depends(get_user_repository)]
UserService = Annotated[UserService_, Depends(get_user_service)]
CurrentUser = Annotated[AuthenticatedUser, Depends(get_auth_middleware_current_user)]
