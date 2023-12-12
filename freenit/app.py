from contextlib import asynccontextmanager
from fastapi import FastAPI

import freenit.config

from .api import api

config = freenit.config.getConfig()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if config.database.is_connected:
        await config.database.disconnect()
    yield
    if not config.database.is_connected:
        await config.database.connect()


app = FastAPI(lifespan=lifespan)
app.mount(config.api_root, api)
