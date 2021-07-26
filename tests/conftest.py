import os
import pytest
from pytest_factoryboy import register
from .factories import UserFactory


register(UserFactory)


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
