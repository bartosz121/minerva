# ruff:  noqa: A001 A002
from typing import Any, Iterable, Literal, TypeVar

from sqlalchemy import Select, delete, select
from sqlalchemy import func as sqla_func
from sqlalchemy.ext.asyncio import AsyncSession

from minerva.core.repository.base import Repository, sql_error_handler
from minerva.core.repository.exceptions import RepositoryError

T = TypeVar("T")
U = TypeVar("U")
SelectT = TypeVar("SelectT", bound=Select[Any])


class SQLAlchemyRepository(Repository[T, U]):
    def __init__(  # noqa: PLR0913
        self,
        session: "AsyncSession",
        *,
        statement: Select[tuple[T]] | None = None,
        auto_expunge: bool = False,
        auto_refresh: bool = True,
        auto_commit: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.session = session
        self.statement = statement if statement is not None else select(self.model)
        self.auto_expunge = auto_expunge
        self.auto_refresh = auto_refresh
        self.auto_commit = auto_commit

    # Session methods

    async def _attach_to_session(self, model: T, strategy: Literal["add", "merge"] = "add") -> T:
        if strategy == "add":
            self.session.add(model)
            return model
        if strategy == "merge":
            return await self.session.merge(model)

        msg = f"Strategy must be 'add' or 'merge', found:{strategy!r}"
        raise RepositoryError(msg)

    async def _flush_or_commit(self, auto_commit: bool | None = None) -> None:
        if auto_commit is None:
            auto_commit = self.auto_commit

        if auto_commit:
            return await self.session.commit()

        return await self.session.flush()

    async def _refresh(
        self,
        instance: T,
        attribute_names: Iterable[str] | None = None,
        *,
        auto_refresh: bool,
        with_for_update: bool | None = None,
    ) -> None:
        if auto_refresh:
            await self.session.refresh(instance, attribute_names=attribute_names, with_for_update=with_for_update)

    async def _expunge(self, instance: T, auto_expunge: bool | None = None) -> None:
        if auto_expunge is None:
            auto_expunge = self.auto_expunge

        if auto_expunge:
            return self.session.expunge(instance)

        return None

    # Statement methods

    async def _where_from_kwargs(self, statement: SelectT, **kwargs: Any) -> SelectT:
        for k, v in kwargs.items():
            statement = statement.where(getattr(self.model, k) == v)
        return statement

    # Repository methods

    async def count(self, **kwargs: Any) -> int:
        """
        Count the number of records in the table. Optionally filter by kwargs.

        Args:
            **kwargs (Any): The kwargs to filter by.

        Returns:
            int: The number of records in the table.
        """
        statement = kwargs.pop("statement", self.statement)
        statement = statement.with_only_columns(sqla_func.count()).select_from(self.model)

        async with sql_error_handler():
            statement = await self._where_from_kwargs(statement, **kwargs)

            result = await self.session.execute(statement)
            return result.scalar_one()

    async def create(self, data: T, **kwargs: Any) -> T:
        auto_commit = kwargs.pop("auto_commit", self.auto_commit)
        auto_refresh = kwargs.pop("auto_refresh", self.auto_refresh)
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)

        async with sql_error_handler():
            instance = await self._attach_to_session(data)
            await self._flush_or_commit(auto_commit=auto_commit)
            await self._refresh(instance, auto_refresh=auto_refresh)
            await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def create_many(self, data: list[T], **kwargs: Any) -> list[T]:
        auto_commit = kwargs.pop("autocommit", self.auto_commit)
        auto_expunge = kwargs.pop("autocommit", self.auto_expunge)

        async with sql_error_handler():
            self.session.add_all(data)
            await self._flush_or_commit(auto_commit=auto_commit)
            for d in data:
                await self._expunge(d, auto_expunge=auto_expunge)
        return data

    async def delete(
        self,
        id: U,
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
    ) -> T:
        async with sql_error_handler():
            instance = await self.get(id)  # raises
            await self.session.delete(instance)
            await self._flush_or_commit(auto_commit=auto_commit)
            await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def delete_many(
        self,
        ids: list[U],
        *,
        auto_commit: bool | None = None,
        auto_expunge: bool | None = None,
    ) -> list[T]:
        async with sql_error_handler():
            instances: list[T] = []
            for id in ids:
                instances.extend(
                    await self.session.scalars(delete(self.model).where(self.model_id_attr == id).returning(self.model))
                )
            await self._flush_or_commit(auto_commit=auto_commit)
            for instance in instances:
                await self._expunge(
                    instance,
                    auto_expunge=auto_expunge,
                )
            return instances

    async def exists(self, **kwargs: Any) -> bool:
        """
        Check if a record exists in the table. Optionally filter by kwargs.

        Args:
            **kwargs (Any): The kwargs to filter by.

        Returns:
            bool: Whether or not the record exists.
        """
        exists = await self.count(**kwargs)
        return exists > 0

    async def get(self, id: U, auto_expunge: bool | None = None, **kwargs: Any) -> T:
        """
        Get a record from the table. Optionally filter by kwargs.

        Args:
            id (U): The ID of the record to get.
            **kwargs (Any): The kwargs to filter by.

        Returns:
            T: The record.
        """
        statement = kwargs.pop("statement", self.statement)
        statement = await self._where_from_kwargs(statement, **kwargs, **{self.model_id_attr_name: id})

        async with sql_error_handler():
            instance = (await self.session.execute(statement)).scalar_one_or_none()
            instance = await self.check_not_found(instance)
            await self._expunge(instance, auto_expunge=auto_expunge)

            return instance

    async def get_one(self, id: U, **kwargs: Any) -> T:
        """
        Get one record from the table. Optionally filter by kwargs.

        Args:
            id (U): The ID of the record to get.

        Returns:
            T: The record.
        """
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)

        async with sql_error_handler():
            instance = (await self.session.execute(self.statement.where(self.model_id_attr == id))).scalar_one_or_none()
            instance = await self.check_not_found(instance)
            await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def get_one_or_none(self, id: U, **kwargs: Any) -> T | None:
        """
        Get one or none records from the table. Optionally filter by kwargs.

        Args:
            id (U): The ID of the record to get.

        Returns:
            T | None: The record.
        """
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)

        async with sql_error_handler():
            instance = (await self.session.execute(self.statement.where(self.model_id_attr == id))).scalar_one_or_none()
            if instance:
                await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def list_(self, **kwargs: Any) -> list[T]:
        """
        List records from the table. Optionally filter by kwargs.

        Args:
            **kwargs (Any): The kwargs to filter by.

        Returns:
            list[T]: The records.
        """
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        statement = kwargs.pop("statement", self.statement)
        statement = await self._where_from_kwargs(statement, **kwargs)

        async with sql_error_handler():
            items = list((await self.session.execute(statement)).scalars())
            for item in items:
                await self._expunge(item, auto_expunge=auto_expunge)

            return items

    async def list_and_count(
        self,
        **kwargs: Any,
    ) -> tuple[list[T], int]:
        """
        List records from the table. Optionally filter by kwargs.

        Args:
            **kwargs (Any): The kwargs to filter by.

        Returns:
            tuple[list[T], int]: The records and the count of the records.
        """
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        statement = kwargs.pop("statement", self.statement)
        statement = await self._where_from_kwargs(statement, **kwargs)
        count_statement = statement.with_only_columns(sqla_func.count()).select_from(self.model)

        async with sql_error_handler():
            count_result = (await self.session.execute(count_statement)).scalar_one()
            items = list((await self.session.execute(statement)).scalars())

            for item in items:
                await self._expunge(item, auto_expunge=auto_expunge)
            return (items, count_result)

    async def update(
        self,
        data: T,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        **kwargs: Any,
    ) -> T:
        auto_commit = kwargs.pop("auto_commit", self.auto_commit)
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        auto_refresh = kwargs.pop("auto_refresh", self.auto_refresh)

        async with sql_error_handler():
            data_id = getattr(data, self.model_id_attr_name)
            await self.get(data_id)  # raises `NotFound`
            instance = await self._attach_to_session(data, strategy="merge")
            await self._flush_or_commit(auto_commit=auto_commit)
            await self._refresh(
                instance,
                attribute_names=attribute_names,
                with_for_update=with_for_update,
                auto_refresh=auto_refresh,
            )
            await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    # TODO: many at once
    async def update_many(
        self,
        data: list[T],
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        **kwargs: Any,
    ) -> list[T]:
        auto_commit = kwargs.pop("auto_commit", self.auto_commit)
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        auto_refresh = kwargs.pop("auto_refresh", self.auto_refresh)

        instances: list[T] = []
        async with sql_error_handler():
            for d in data:
                instance = await self._attach_to_session(d, strategy="merge")
                await self._flush_or_commit(auto_commit=auto_commit)
                await self._refresh(
                    instance,
                    attribute_names=attribute_names,
                    with_for_update=with_for_update,
                    auto_refresh=auto_refresh,
                )
                await self._expunge(instance, auto_expunge=auto_expunge)
                instances.append(instance)
            return instances

    async def upsert(
        self,
        data: T,
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        **kwargs: Any,
    ) -> T:
        """
        Update or insert a record in the table.

        Args:
            data (T): The data to update or insert the record with.
            attribute_names (Iterable[str] | None): The attribute names to update
            or insert the record with.
            with_for_update (bool | None): Whether or not to use FOR UPDATE.
            **kwargs (Any): The kwargs to filter by.

        Returns:
            T: The updated or inserted record.
        """
        auto_commit = kwargs.pop("auto_commit", self.auto_commit)
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        auto_refresh = kwargs.pop("auto_refresh", self.auto_refresh)

        async with sql_error_handler():
            instance = await self._attach_to_session(data, strategy="merge")
            await self._flush_or_commit(auto_commit=auto_commit)
            await self._refresh(
                instance,
                attribute_names=attribute_names,
                with_for_update=with_for_update,
                auto_refresh=auto_refresh,
            )
            await self._expunge(instance, auto_expunge=auto_expunge)
            return instance

    async def upsert_many(
        self,
        data: list[T],
        attribute_names: Iterable[str] | None = None,
        with_for_update: bool | None = None,
        **kwargs: Any,
    ) -> list[T]:
        auto_commit = kwargs.pop("auto_commit", self.auto_commit)
        auto_expunge = kwargs.pop("auto_expunge", self.auto_expunge)
        auto_refresh = kwargs.pop("auto_refresh", self.auto_refresh)

        instances: list[T] = []
        async with sql_error_handler():
            for d in data:
                instance = await self._attach_to_session(d, strategy="merge")
                await self._flush_or_commit(auto_commit=auto_commit)
                await self._refresh(
                    instance,
                    attribute_names=attribute_names,
                    with_for_update=with_for_update,
                    auto_refresh=auto_refresh,
                )
                await self._expunge(instance, auto_expunge=auto_expunge)
                instances.append(instance)

            return instances
