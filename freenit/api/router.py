from fastapi import FastAPI
from ..config import getConfig


config = getConfig()
api = FastAPI()
api.state.database = config.database


@api.on_event("startup")
async def startup() -> None:
    database_ = api.state.database
    if not database_.is_connected:
        await database_.connect()


@api.on_event("shutdown")
async def shutdown() -> None:
    database_ = api.state.database
    if database_.is_connected:
        await database_.disconnect()
