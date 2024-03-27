from sqlalchemy.ext.asyncio import async_sessionmaker

from minerva.core.db.engine import engine

session = async_sessionmaker(engine, expire_on_commit=False)
