import importlib
import os

import pytest
from pytest_factoryboy import register

from alembic import command
from alembic.config import Config
from name import app_name

from .factories import UserFactory

alembic_cfg = Config("alembic.ini")
register(UserFactory)


@pytest.fixture
def db_setup():
    app = importlib.import_module(f"{app_name}.app")

    command.upgrade(alembic_cfg, "head")

    yield app.app

    current_path = os.path.dirname(__file__)
    os.remove(f"{current_path}/../test.sqlite")
