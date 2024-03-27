import pytest
from sqlalchemy.sql import select, text

from minerva.core.service import exceptions as service_exceptions
from tests._utils import TodoItem, TodoItemService
from tests.conftest import DUMMY_COUNT


async def test_service_sqlalchemy_count(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):  # noqa: ARG001
    count = await todo_item_service.count()
    assert count == DUMMY_COUNT


async def test_service_sqlalchemy_create(faker, session, todo_item_service: TodoItemService):
    item = TodoItem(title=faker.word(), description=faker.sentence(), is_completed=False)
    created = await todo_item_service.create(item)
    assert created

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.title == item.title))).scalar_one_or_none()
    assert item_from_db is not None
    assert item_from_db.id == created.id


async def test_service_sqlalchemy_create_many(session, faker, todo_item_service: TodoItemService):
    items = [TodoItem(title=f"Create many {i}", description=faker.sentence(), is_completed=False) for i in range(10)]
    created = await todo_item_service.create_many(items)
    assert len(created) == len(items)

    items_from_db = (await session.execute(select(TodoItem).where(TodoItem.title.like("Create many%")))).scalars().all()

    assert len(items_from_db) == len(items)
    assert all(item.id in [i.id for i in items_from_db] for item in items)


async def test_service_sqlalchemy_delete(session, insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item = insert_dummy[0]

    await todo_item_service.delete(item.id)

    should_be_none = (await session.execute(select(TodoItem).where(TodoItem.id == item.id))).scalar_one_or_none()
    assert should_be_none is None


async def test_service_sqlalchemy_delete_many(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    items = insert_dummy[:5]

    await todo_item_service.delete_many([item.id for item in items])


# TODO: is it possible to make repository.where rom kwargs type safe?
async def test_service_sqlalchemy_exists(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item = insert_dummy[0]
    result = await todo_item_service.exists(id=item.id)
    assert result is True


async def test_service_sqlalchemy_exists_false(todo_item_service: TodoItemService):
    result = await todo_item_service.exists(id=999999)
    assert result is False


async def test_service_sqlalchemy_get(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item_ = insert_dummy[0]

    item = await todo_item_service.get(item_.id)
    assert item
    assert item.id == item_.id


async def test_service_sqlalchemy_get_raises_not_found(todo_item_service: TodoItemService):
    with pytest.raises(service_exceptions.NotFoundError):
        await todo_item_service.get(99999)


async def test_service_sqlalchemy_get_one(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item_ = insert_dummy[0]

    item = await todo_item_service.get_one(id=item_.id, title=item_.title)
    assert item
    assert item.id == item_.id
    assert item.title == item_.title


async def test_service_sqlalchemy_get_one_raises_not_found(todo_item_service: TodoItemService):
    with pytest.raises(service_exceptions.NotFoundError):
        await todo_item_service.get(99999)


async def test_service_sqlalchemy_get_one_or_none(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item_ = insert_dummy[0]

    item = await todo_item_service.get_one_or_none(item_.id)
    assert item
    assert item.id == item_.id


async def test_service_sqlalchemy_get_one_or_none_returns_none(todo_item_service: TodoItemService):
    item = await todo_item_service.get_one_or_none(99999)
    assert item is None


async def test_service_sqlalchemy_list_(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    items = await todo_item_service.list_()
    assert items
    assert len(items) == len(insert_dummy)


async def test_service_sqlalchemy_list_and_count(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    items_and_count = await todo_item_service.list_and_count()

    assert len(items_and_count[0]) == len(insert_dummy)
    assert items_and_count[1] == len(insert_dummy)


async def test_service_sqlalchemy_update(insert_dummy: list[TodoItem], todo_item_service: TodoItemService):
    item_ = insert_dummy[0]
    item_.title = "Updated"

    item = await todo_item_service.update(item_)
    assert item
    assert item.title == item_.title


async def test_service_sqlalchemy_update_raises_not_found(todo_item_service: TodoItemService):
    with pytest.raises(service_exceptions.NotFoundError):
        item = TodoItem(id=99999, title="Item")
        await todo_item_service.update(item)


async def test_service_sqlalchemy_update_many(
    session, insert_dummy: list[TodoItem], todo_item_service: TodoItemService
):
    items_ = insert_dummy[:10]
    for i, item in enumerate(items_):
        item.title = f"Updated {i}"

    updated = await todo_item_service.update_many(items_)
    assert updated

    items_from_db = (await session.execute(select(TodoItem).where(TodoItem.title.like("Updated%")))).scalars().all()

    assert len(items_from_db) == len(items_)
    assert all(item.title in [i.title for i in items_from_db] for item in items_)


async def test_service_sqlalchemy_upsert_create(session, faker, todo_item_service: TodoItemService):
    item = TodoItem(title="Upsert create", description=faker.word(), is_completed=True)

    created = await todo_item_service.upsert(item)
    assert created

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.title == item.title))).scalars().all()
    assert item_from_db


async def test_service_sqlalchemy_upsert_update(
    session, insert_dummy: list[TodoItem], todo_item_service: TodoItemService
):
    item_ = insert_dummy[0]
    item_.title = "Upsert create"

    updated = await todo_item_service.upsert(item_)
    assert updated

    item_from_db = (await session.execute(select(TodoItem).where(TodoItem.title == item_.title))).scalars().all()
    assert item_from_db


async def test_service_sqlalchemy_upsert_many_create(session, todo_item_service: TodoItemService):
    items = [TodoItem(title=f"Test upsert {i}", description="test upsert desc", is_completed=False) for i in range(10)]

    created = await todo_item_service.upsert_many(items)
    assert len(created) == len(items)

    items_from_db = (await session.execute(select(TodoItem).where(TodoItem.title.like("Test upsert%")))).scalars().all()
    assert len(items_from_db) == len(items)


async def test_service_sqlalchemy_upsert_many_update(
    session, insert_dummy: list[TodoItem], todo_item_service: TodoItemService
):
    items_ = insert_dummy[:10]
    for i, item in enumerate(items_):
        item.title = f"Upsert update {i}"

    updated = await todo_item_service.upsert_many(items_)
    assert len(updated) == len(items_)

    item_from_db = (
        (await session.execute(select(TodoItem).where(TodoItem.title.like("Upsert update %")))).scalars().all()
    )
    assert item_from_db
