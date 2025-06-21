import os

import pytest

from alembic.config import Config
from migrate import db_setup as dbs

from .client import Client

alembic_cfg = Config("alembic.ini")

os.environ["FREENIT_ENV"] = "test"


@pytest.fixture
def db_setup():
    app = dbs()

    yield app.app

    current_path = os.path.dirname(__file__)
    os.remove(f"{current_path}/../test.sqlite")


@pytest.fixture
def client(db_setup):
    return Client(db_setup)
