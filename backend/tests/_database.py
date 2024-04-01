import asyncio
from contextlib import contextmanager

from sqlalchemy.ext.asyncio import async_scoped_session, async_sessionmaker
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from minerva.core.config import settings

Session = async_scoped_session(async_sessionmaker(expire_on_commit=False), scopefunc=asyncio.current_task)
SessionSync = scoped_session(sessionmaker(expire_on_commit=False))


@contextmanager
def init_test_database():
    assert "test" in settings.DB_DATABASE.lower()

    db_sync_uri = str(settings.DB_URI_SYNC)

    if database_exists(db_sync_uri):
        drop_database(db_sync_uri)

    create_database(db_sync_uri)

    try:
        yield
    finally:
        drop_database(db_sync_uri)
