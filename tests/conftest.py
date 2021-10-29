import os
import pytest
from pytest_factoryboy import register
from .factories import UserFactory, SuperUserFactory
from .client import Client

register(UserFactory)
register(SuperUserFactory)


@pytest.fixture
def db_setup():
    from freenit.app import app as fastapp
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield fastapp

    current_path = os.path.dirname(__file__)
    os.remove(f'{current_path}/../test.sqlite')


@pytest.fixture
def client(db_setup):
    return Client(db_setup)
