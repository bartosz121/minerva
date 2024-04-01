import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import EmailStr
from pydantic.functional_validators import AfterValidator

from minerva.core.schemas import MinervaBaseModel

PASSWORD_REGEX = re.compile(r"^(?=.*[\d])(?=.*[!@#$%^&*()_+])[\w!@#$%^&*()_+]{6,128}$")


def validate_password_complexity(password: str) -> str:
    if not re.match(PASSWORD_REGEX, password):
        msg = (
            "Password must contain at least one digit"
            " and one special character from the set !@#$%^&*()_+"
            " and be between 6 and 128 characters long"
        )
        raise ValueError(msg)
    return password


Password = Annotated[str, AfterValidator(validate_password_complexity)]


class UserBase(MinervaBaseModel):
    email: EmailStr


class UserSignUpIn(UserBase):
    password: Password


class UserRead(UserBase):
    id: UUID


class SignInResponse(MinervaBaseModel):
    token: str
    expiration_date: datetime
