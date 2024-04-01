# ruff: noqa: EM101
from fastapi import APIRouter, Request, Response, status
from starlette.authentication import requires

from minerva.access_token import dependencies as access_token_deps
from minerva.access_token import models as access_token_models
from minerva.core import exceptions as http_exceptions
from minerva.core.config import settings
from minerva.users import dependencies as user_deps
from minerva.users import exceptions, schemas, security

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserRead,
    responses={409: {"description": "User with this email address already exists"}},
)
async def sign_up(user_service: user_deps.UserService, data: schemas.UserSignUpIn):
    try:
        user = await user_service.create_from_schema(data)
    except exceptions.EmailAlreadyExistsError as exc:
        raise http_exceptions.Conflict("User with this email address already exists") from exc
    else:
        return user


@router.post(
    "/sign-in",
    response_model=schemas.SignInResponse,
    responses={400: {"description": "User with given email doesn't exist or password is wrong"}},
)
async def sign_in(
    response: Response,
    access_token_service: access_token_deps.AccessTokenService,
    user_service: user_deps.UserService,
    data: schemas.UserSignUpIn,
):
    user = await user_service.get_one_or_none_by_email(data.email)
    if not user:
        raise http_exceptions.BadRequest("User with this email address doesn't exist")

    is_password_correct = security.verify_password(data.password, hashed_password=user.hashed_password)
    if not is_password_correct:
        raise http_exceptions.BadRequest("Wrong password")

    token = await access_token_service.create(access_token_models.AccessToken(user_id=user.id))

    response.set_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        token.token,
        max_age=token.expiration_date_int_from_now,
        samesite="lax",
        httponly=settings.ENVIRONMENT.is_production,
        secure=settings.ENVIRONMENT.is_production,
    )

    return {"token": token.token, "expiration_date": token.expiration_date}


@router.get("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
@requires("authenticated")
async def sign_out(request: Request, response: Response):  # noqa: ARG001
    response.delete_cookie(
        settings.ACCESS_TOKEN_COOKIE_NAME,
        samesite="lax",
        httponly=settings.ENVIRONMENT.is_production,
        secure=settings.ENVIRONMENT.is_production,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
