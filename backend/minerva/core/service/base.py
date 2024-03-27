# ruff: noqa: A002
from typing import Any, Generic, TypeVar

from minerva.core.repository import exceptions as repository_exceptions
from minerva.core.repository.base import Repository
from minerva.core.service import exceptions as service_exceptions

T = TypeVar("T")
U = TypeVar("U")


class Service(Generic[T, U]):
    def __init__(self, repository: Repository[T, U]) -> None:
        """# Override this and set `self.repository` to some `Repository` subclass"""
        self.repository = repository

    async def count(self, **kwargs: Any) -> int:
        return await self.repository.count(**kwargs)

    async def create(self, data: T) -> T:
        return await self.repository.create(data)

    async def create_many(self, data: list[T]) -> list[T]:
        return await self.repository.create_many(data)

    async def delete(self, id: U) -> T:
        try:
            return await self.repository.delete(id)
        except repository_exceptions.NotFoundError as exc:
            raise service_exceptions.NotFoundError() from exc

    async def delete_many(self, ids: list[U]) -> list[T]:
        return await self.repository.delete_many(ids)

    async def exists(self, **kwargs: Any) -> bool:
        return await self.repository.exists(**kwargs)

    async def get(self, id: U) -> T:
        try:
            return await self.repository.get(id)
        except repository_exceptions.NotFoundError as exc:
            raise service_exceptions.NotFoundError() from exc

    async def get_one(self, id: U, **kwargs: Any) -> T:
        try:
            return await self.repository.get_one(id, **kwargs)
        except repository_exceptions.NotFoundError as exc:
            raise service_exceptions.NotFoundError() from exc

    async def get_one_or_none(self, id: U, **kwargs: Any) -> T | None:
        return await self.repository.get_one_or_none(id, **kwargs)

    async def list_(self, **kwargs: Any) -> list[T]:
        return await self.repository.list_(**kwargs)

    async def list_and_count(self, **kwargs: Any) -> tuple[list[T], int]:
        return await self.repository.list_and_count(**kwargs)

    async def update(self, data: T) -> T:
        try:
            return await self.repository.update(data)
        except repository_exceptions.NotFoundError as exc:
            raise service_exceptions.NotFoundError() from exc

    async def update_many(self, data: list[T]) -> list[T]:
        return await self.repository.update_many(data)

    async def upsert(self, data: T) -> T:
        return await self.repository.upsert(data)

    async def upsert_many(self, data: list[T]) -> list[T]:
        return await self.repository.upsert_many(data)
