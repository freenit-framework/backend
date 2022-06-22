import importlib
import os

import pytest

from alembic import command
from alembic.config import Config
from name import app_name

from .client import Client

alembic_cfg = Config("alembic.ini")

os.environ["FREENIT_ENV"] = "test"


@pytest.fixture
def db_setup():
    app = importlib.import_module(f"{app_name}.app")
    command.upgrade(alembic_cfg, "head")

    yield app.app

    current_path = os.path.dirname(__file__)
    os.remove(f"{current_path}/../test.sqlite")


@pytest.fixture
def client(db_setup):
    return Client(db_setup)
