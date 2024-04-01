from logging import getLogger
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from minerva.core.db.main import session as db_session
from minerva.core.exceptions import MinervaError
from minerva.core.repository.exceptions import RepositoryError
from minerva.core.service.exceptions import ServiceError

log = getLogger(__name__)


async def get_session():
    async with db_session() as session:
        async with session.begin():
            try:
                yield session
            except (MinervaError, RepositoryError, ServiceError) as exc:
                log.error(str(exc))
                await session.rollback()
                raise exc


DbSession = Annotated[AsyncSession, Depends(get_session)]
