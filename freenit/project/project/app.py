from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import getConfig

from .api import api

config = getConfig()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not config.database.connected:
        await config.database.connect()
    yield
    if config.database.connected:
        await config.database.disconnect()


app = FastAPI(lifespan=lifespan)
app.mount(config.api_root, api)

if "git" in config.modules:
    from freenit.api.git_http import router as git_http_router

    app.include_router(git_http_router)
