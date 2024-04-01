# ruff: noqa: N802

from enum import StrEnum

from pydantic import SecretStr, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "LOCAL"
    TESTING = "TESTING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

    @property
    def is_local(self) -> bool:
        return self == "LOCAL"

    @property
    def is_testing(self) -> bool:
        return self == "TESTING"

    @property
    def is_staging(self) -> bool:
        return self == "STAGING"

    @property
    def is_debug(self) -> bool:
        return self in {Environment.LOCAL, Environment.TESTING, Environment.STAGING}

    @property
    def is_production(self) -> bool:
        return self == "PRODUCTION"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            ".env.prod",
        ),
        env_ignore_empty=True,
        extra="ignore",
    )

    ACCESS_TOKEN_COOKIE_NAME: str = "minerva_auth"
    ACCESS_TOKEN_DURATION: int = 3600

    ENVIRONMENT: Environment = Environment.LOCAL

    DB_HOST: str
    DB_PORT: int = 5432
    DB_DATABASE: str
    DB_USER: str
    DB_PASSWORD: SecretStr

    def _db_uri(self, *, async_: bool = True) -> MultiHostUrl:
        return MultiHostUrl.build(
            scheme=f"postgresql+{'asyncpg' if async_ else 'psycopg'}",
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_DATABASE,
        )

    @computed_field
    def DB_URI(self) -> MultiHostUrl:
        return self._db_uri()

    @computed_field
    def DB_URI_SYNC(self) -> MultiHostUrl:
        return self._db_uri(async_=False)


settings = Settings()  # type: ignore
