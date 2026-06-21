import asyncio
import os
import subprocess  # nosec: B404
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .config import getConfig

from .api import api

config = getConfig()


def _run_migrations() -> None:
    env = os.environ.copy()
    env.setdefault("FREENIT_ENV", "prod")
    subprocess.run(["oxyde", "migrate"], check=True, env=env)  # nosec


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.environ.get("FREENIT_ENV") != "test":
        await asyncio.to_thread(_run_migrations)
    if not config.database.connected:
        await config.database.connect()
    yield
    if config.database.connected:
        await config.database.disconnect()


app = FastAPI(lifespan=lifespan)
app.mount(config.api_root, api)

if "git" in config.modules:
    from .api.git_http import router as git_http_router

    app.include_router(git_http_router)
