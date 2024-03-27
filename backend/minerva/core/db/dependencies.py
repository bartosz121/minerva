from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from minerva.core.db.main import session


async def db_session():
    async with session() as session_:
        yield session_


DbSession = Annotated[AsyncSession, Depends(db_session)]
