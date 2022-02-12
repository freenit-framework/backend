from fastapi import FastAPI

from .api import api
from .config import getConfig

config = getConfig()
app = FastAPI()


@app.on_event("startup")
async def startup() -> None:
    if not config.database.is_connected:
        await config.database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    if config.database.is_connected:
        await config.database.disconnect()


app.mount("/api/v1", api)
