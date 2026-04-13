import os
import asyncio
import tempfile
from pathlib import Path

os.environ["FREENIT_ENV"] = "test"

import pytest
import oxyde
from migrate import db_setup as dbs
from freenit.app import config

from .client import Client


@pytest.fixture
def db_setup():
    asyncio.run(config.database.disconnect())
    fd, db_path = tempfile.mkstemp(suffix=".sqlite", dir=Path(__file__).resolve().parent.parent)
    os.close(fd)
    if os.path.exists(db_path):
        os.remove(db_path)
    dburl = f"sqlite:///{Path(db_path).resolve()}"
    os.environ["FREENIT_DBURL"] = dburl
    config.dburl = dburl
    config.database = oxyde.AsyncDatabase(dburl, overwrite=True)

    app = dbs()

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
