from fastapi import FastAPI

from ..config import getConfig
from ..decorators import FreenitAPI

api = FastAPI()
route = FreenitAPI(api)


@api.on_event("startup")
async def startup():
    config = getConfig()
    if not config.database.is_connected:
        await config.database.connect()


@api.on_event("shutdown")
async def shutdown():
    config = getConfig()
    if config.database.is_connected:
        await config.database.disconnect()
