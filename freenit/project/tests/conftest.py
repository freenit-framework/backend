import importlib
import os
import asyncio
import tempfile
from pathlib import Path

import pytest
import oxyde
from name import app_name
from migrate import run_migrations

from .client import Client

os.environ["FREENIT_ENV"] = "test"


@pytest.fixture
def db_setup():
    config = importlib.import_module(f"{app_name}.app").config
    asyncio.run(config.database.disconnect())
    fd, db_path = tempfile.mkstemp(
        suffix=".sqlite",
        dir=Path(__file__).resolve().parent.parent,
    )
    os.close(fd)
    if os.path.exists(db_path):
        os.remove(db_path)
    dburl = f"sqlite:///{Path(db_path).resolve()}"
    os.environ["FREENIT_DBURL"] = dburl
    config.dburl = dburl
    config.database = oxyde.AsyncDatabase(dburl, overwrite=True)

    app = importlib.import_module(f"{app_name}.app")
    run_migrations()

    yield app.app

    asyncio.run(config.database.disconnect())
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ.pop("FREENIT_DBURL", None)


@pytest.fixture
def client(db_setup):
    client = Client(db_setup)
    yield client
    client.close()
