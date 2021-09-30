from fastapi import FastAPI
from ..config import getConfig

api = FastAPI()


@api.on_event("startup")
async def startup() -> None:
    config = getConfig()
    if not config.database.is_connected:
        await config.database.connect()


@api.on_event("shutdown")
async def shutdown() -> None:
    config = getConfig()
    if config.database.is_connected:
        await config.database.disconnect()
