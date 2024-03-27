from contextlib import asynccontextmanager

from fastapi import FastAPI

from minerva.core.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    yield
    await engine.dispose()
