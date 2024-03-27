# ruff: noqa: ARG001
from unittest import mock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from minerva.core.repository.exceptions import NotFoundError, RepositoryError
from minerva.core.repository.sqlalchemy import SQLAlchemyRepository
from tests._utils import TodoItem, TodoItemRepository
from tests.conftest import DUMMY_COUNT


async def test_sqlalchemy_repository_attach_to_session_raises_repository_exception_on_wrong_strategy(
    sqlalchemy_repository_mock: SQLAlchemyRepository,
):
    with pytest.raises(RepositoryError, match="Strategy must be 'add' or 'merge', found:"):
        await sqlalchemy_repository_mock._attach_to_session(
            mock.MagicMock(),
            "unknwn",  # type: ignore[misc]
        )


async def test_sqlalchemy_flush_or_commit_commit_if_auto_commit(
    sqlalchemy_repository_mock: SQLAlchemyRepository,
):
    await sqlalchemy_repository_mock._flush_or_commit(auto_commit=True)
    sqlalchemy_repository_mock.session.commit.assert_called_once()  # type: ignore[misc]


async def test_sqlalchemy_refresh_refresh_not_called_if_auto_refresh_is_false(
    sqlalchemy_repository_mock: SQLAlchemyRepository,
):
    await sqlalchemy_repository_mock._refresh(mock.MagicMock(), auto_refresh=False)
    sqlalchemy_repository_mock.session.refresh.assert_not_called()  # type: ignore[misc]


async def test_sqlalchemy_expunge_expunge_called_if_auto_expunge_is_true(
    sqlalchemy_repository_mock: SQLAlchemyRepository,
):
    await sqlalchemy_repository_mock._expunge(mock.MagicMock(), auto_expunge=True)
    sqlalchemy_repository_mock.session.expunge.assert_called_once()  # type: ignore[misc]


async def test_count(insert_dummy, todo_item_repository: TodoItemRepository):
    repo_count = await todo_item_repository.count()
    assert repo_count == DUMMY_COUNT


async def test_count_kwargs(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test count kwargs",
        description="test count kwargs desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    repo_count = await todo_item_repository.count(
        title=item.title,
        description=item.description,
        is_completed=item.is_completed,
    )
    assert repo_count == 1


async def test_create(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test create",
        description="test create desc",
        is_completed=False,
    )
    created = await todo_item_repository.create(item)
    assert created == item
    assert created.id

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.title == "Test create"))).scalar_one_or_none()
    assert item_from_db is not None
    assert item_from_db.id == created.id


async def test_create_many(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [
        TodoItem(
            title=f"Test create_many {i}",
            description=f"test create_many {i}",
            is_completed=False,
        )
        for i in range(10)
    ]

    created = await todo_item_repository.create_many(items)
    assert created == items
    assert all(item.id for item in created)

    items_from_db = (
        (await session.execute(select(TodoItem).where(TodoItem.title.like("Test create_many%")))).scalars().all()
    )

    assert len(items_from_db) == len(items)
    assert all(item.id in [i.id for i in items_from_db] for item in items)


async def test_delete(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test delete",
        description="test delete desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    deleted = await todo_item_repository.delete(item.id)
    assert deleted == item

    should_be_none = (await session.execute(select(TodoItem).where(TodoItem.id == item.id))).scalar_one_or_none()
    assert should_be_none is None


async def test_delete_raises_not_found(session: AsyncSession, todo_item_repository: TodoItemRepository):
    with pytest.raises(NotFoundError):
        await todo_item_repository.delete(454544545)


# Check your sqlite version if this fails, delete_many uses
# `RETURNING` which is supported in 3.35.0+
async def test_delete_many(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [
        TodoItem(
            title=f"Test delete_many {i}",
            description=f"test delete_many {i}",
            is_completed=False,
        )
        for i in range(10)
    ]

    session.add_all(items)
    await session.commit()

    deleted = await todo_item_repository.delete_many([item.id for item in items])
    assert len(deleted) == len(items)
    assert all(item.title in [i.title for i in deleted] for item in items)

    items_from_db = (
        (await session.execute(select(TodoItem).where(TodoItem.title.like("Test delete_many%")))).scalars().all()
    )
    assert items_from_db == []


async def test_exists(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test exists",
        description="test exists desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    assert (await todo_item_repository.exists(id=item.id)) is True
    assert (await todo_item_repository.exists(title=item.title)) is True
    assert (await todo_item_repository.exists(description=item.description)) is True


async def test_exists_false(todo_item_repository: TodoItemRepository):
    assert (await todo_item_repository.exists(id=999999)) is False
    assert (await todo_item_repository.exists(title="Test exists")) is False
    assert (await todo_item_repository.exists(description="test exists desc")) is False


async def test_get(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test get",
        description="test get desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    item_from_db = await todo_item_repository.get(item.id)
    assert vars(item) == vars(item_from_db)


async def test_get_raises_not_found(todo_item_repository: TodoItemRepository):
    with pytest.raises(NotFoundError):
        await todo_item_repository.get(999999)


async def test_get_one_raises_not_found(
    session: AsyncSession,
    todo_item_repository: TodoItemRepository,
):
    with pytest.raises(NotFoundError):
        await todo_item_repository.get_one(999999)


async def test_get_one(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test get_one",
        description="test get_one desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    item_from_db = await todo_item_repository.get_one(item.id)
    assert vars(item) == vars(item_from_db)


async def test_get_one_or_none(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(
        title="Test get_one_or_none",
        description="test get_one_or_none desc",
        is_completed=False,
    )
    session.add(item)
    await session.commit()

    item_from_db = await todo_item_repository.get_one_or_none(item.id)
    assert vars(item) == vars(item_from_db)

    none_item_from_db = await todo_item_repository.get_one_or_none(999999)
    assert none_item_from_db is None


async def test_list_(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [
        TodoItem(
            title=f"Test list {i}",
            description="test list",
            is_completed=False,
        )
        for i in range(100)
    ]

    session.add_all(items)
    await session.commit()

    items_from_db = await todo_item_repository.list_(description="test list")
    assert len(items_from_db) == len(items)
    assert all(item.title in [i.title for i in items_from_db] for item in items)


async def test_list_and_count(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [
        TodoItem(
            title=f"Test list {i}",
            description="test list",
            is_completed=False,
        )
        for i in range(100)
    ]

    session.add_all(items)
    await session.commit()

    items_from_db, count = await todo_item_repository.list_and_count(description="test list")
    assert len(items_from_db) == len(items)
    assert all(item.title in [i.title for i in items_from_db] for item in items)
    assert count == len(items)


async def test_update(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(title="Test update", description="test update desc", is_completed=False)
    session.add(item)
    await session.commit()

    item.title = "Test update updated"
    await todo_item_repository.update(item)

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.id == item.id))).scalar_one_or_none()
    assert item_from_db is not None
    assert item_from_db.title == "Test update updated"


async def test_update_raises_not_found(session: AsyncSession, todo_item_repository: TodoItemRepository):
    with pytest.raises(NotFoundError):
        await todo_item_repository.update(TodoItem(id=123123123, title="title", is_completed=False))


async def test_update_many(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [TodoItem(title=f"Test update {i}", description="test update desc", is_completed=False) for i in range(10)]
    session.add_all(items)
    await session.commit()

    for i, item in enumerate(items):
        item.title = f"Test update updated {i}"

    await todo_item_repository.update_many(items)

    items_from_db = (
        (await session.execute(select(TodoItem).where(TodoItem.title.like("Test update updated%")))).scalars().all()
    )

    assert len(items_from_db) == len(items)
    assert all(item.title in [i.title for i in items_from_db] for item in items)


async def test_upsert_create(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(title="Test upsert", description="test upsert desc", is_completed=False)
    upserted = await todo_item_repository.upsert(item)

    assert upserted.id

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.id == upserted.id))).scalar_one_or_none()
    assert item_from_db is not None
    assert item_from_db.id == upserted.id


async def test_upsert_update(session: AsyncSession, todo_item_repository: TodoItemRepository):
    item = TodoItem(title="Test upsert", description="test upsert desc", is_completed=False)
    session.add(item)
    await session.commit()

    item.title = "Test upsert updated"

    upserted = await todo_item_repository.upsert(item)

    assert upserted == item
    assert upserted.title == "Test upsert updated"

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.id == upserted.id))).scalar_one_or_none()
    assert item_from_db is not None
    assert item_from_db.title == "Test upsert updated"


async def test_upsert_many_create(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [TodoItem(title=f"Test upsert {i}", description="test upsert desc", is_completed=False) for i in range(10)]

    upserted = await todo_item_repository.upsert_many(items)
    assert len(upserted) == len(items)
    assert all(item.id for item in upserted)

    items_from_db = (await session.execute(select(TodoItem).where(TodoItem.title.like("Test upsert%")))).scalars().all()
    assert len(items_from_db) == len(items)


async def test_upsert_many_update(session: AsyncSession, todo_item_repository: TodoItemRepository):
    items = [TodoItem(title=f"Test upsert {i}", description="test upsert desc", is_completed=False) for i in range(10)]
    session.add_all(items)
    await session.commit()

    for item in items:
        item.title = "Test upsert updated"

    upserted = await todo_item_repository.upsert_many(items)
    assert len(upserted) == len(items)

    items_from_db = (await session.execute(select(TodoItem).where(TodoItem.title.like("Test upsert%")))).scalars().all()
    assert len(items_from_db) == len(items)
    assert all(item.title == "Test upsert updated" for item in items_from_db)
