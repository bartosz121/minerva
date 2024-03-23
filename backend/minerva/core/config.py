# ruff: noqa: N802

from enum import StrEnum

from pydantic import PostgresDsn, computed_field
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
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    ENVIRONMENT: Environment = Environment.LOCAL

    DB_HOST: str
    DB_PORT: int = 5432
    DB_DATABASE: str
    DB_USER: str
    DB_PASSWORD: str

    @computed_field
    def DB_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_DATABASE,
        )
