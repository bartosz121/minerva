# ruff: noqa: A002

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from logging import getLogger
from typing import Any, Generic, TypeVar

from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from minerva.core.repository.exceptions import ConflictError, NotFoundError, RepositoryError

log = getLogger(__name__)


@asynccontextmanager
async def sql_error_handler():
    try:
        yield
    except IntegrityError as exc:
        log.error(str(exc))
        raise ConflictError from exc
    except SQLAlchemyError as exc:
        log.error(str(exc))
        msg = "An exception occured while executing SQL statement"
        raise RepositoryError(msg) from exc
    except AttributeError as exc:
        log.error(str(exc))
        raise RepositoryError from exc


T = TypeVar("T")
U = TypeVar("U")


class Repository(Generic[T, U], ABC):
    model: type[T]
    model_id_attr_name: str = "id"
    model_id_type: type[U]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    @property
    def model_id_attr(self) -> Column[U]:
        return getattr(self.model, self.model_id_attr_name)

    @staticmethod
    async def check_not_found(item: T | None) -> T:
        if item is None:
            msg = "No record found"
            raise NotFoundError(msg)
        return item

    @abstractmethod
    async def count(self, **kwargs: Any) -> int:
        """
        Count the number of records in the table.

        Returns:
            int: The number of records in the table.
        """

    @abstractmethod
    async def create(self, data: T) -> T:
        """
        Create a record in the table.

        Args:
            data (T): The data to create the record with.

        Returns:
            T: The created record.
        """

    @abstractmethod
    async def create_many(self, data: list[T]) -> list[T]:
        """
        Create many records in the table.

        Args:
            data (list[T]): The data to create the records with.

        Returns:
            list[T]: The created records.
        """

    @abstractmethod
    async def delete(self, id: U) -> T:
        """
        Delete a record from the table.

        Args:
            id (U): The ID of the record to delete.

        Returns:
            T: The deleted record.

        Raises:
            NotFoundError: If no record is found.
        """

    @abstractmethod
    async def delete_many(self, ids: list[U]) -> list[T]:
        """
        Delete many records from the table.

        Args:
            ids (list[U]): The IDs of the records to delete.

        Returns:
            list[T]: The deleted records.
        """

    @abstractmethod
    async def exists(self, **kwargs: Any) -> bool:
        """
        Check if a record exists in the table.

        Args:
            **kwargs (Any): The query parameters to check for.

        Returns:
            bool: Whether or not the record exists.
        """

    @abstractmethod
    async def get(self, id: U, **kwargs: Any) -> T:
        """
        Get a record from the table.

        Args:
            id (U): The ID of the record to get.
            **kwargs (Any): The query parameters to get the record with.

        Returns:
            T: The record.

        Raises:
            NotFoundError: If no record is found.
        """

    @abstractmethod
    async def get_one(self, id: U, **kwargs: Any) -> T:
        """
        Get a record from the table.

        Args:
            id (U): The ID of the record to get.
            **kwargs (Any): The query parameters to get the record with.

        Returns:
            T: The record.

        Raises:
            NotFoundError: If no record is found.
        """

    @abstractmethod
    async def get_one_or_none(self, id: U, **kwargs: Any) -> T | None:
        """
        Get a record from the table.

        Args:
            id (U): The ID of the record to get.
            **kwargs (Any): The query parameters to get the record with.

        Returns:
            T | None: The record.
        """

    @abstractmethod
    async def list_(self, **kwargs: Any) -> list[T]:
        """
        List records from the table.

        Args:
            **kwargs (Any): The query parameters to list the records with.

        Returns:
            list[T]: The records.
        """

    @abstractmethod
    async def list_and_count(self, **kwargs: Any) -> tuple[list[T], int]:
        """
        List records from the table.

        Args:
            **kwargs (Any): The query parameters to list the records with.

        Returns:
            tuple[list[T], int]: The records and the count.
        """

    @abstractmethod
    async def update(self, data: T) -> T:
        """
        Update a record in the table.

        Args:
            data (T): The data to update the record with.

        Returns:
            T: The updated record.

        Raises:
            NotFoundError: If no record is found.
        """

    @abstractmethod
    async def update_many(self, data: list[T]) -> list[T]:
        """
        Update many records in the table.

        Args:
            data (list[T]): The data to update the records with.

        Returns:
            list[T]: The updated records.
        """

    @abstractmethod
    async def upsert(self, data: T) -> T:
        """
        Upsert a record in the table.

        Args:
            data (T): Instance of the model to upsert.

        Returns:
            T: The upserted record.
        """

    @abstractmethod
    async def upsert_many(self, data: list[T]) -> list[T]:
        """
        Upsert many records in the table.

        Args:
            data (list[T]): List of instances of the model to upsert.

        Returns:
            list[T]: The upserted records.
        """
