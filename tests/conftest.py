import os
from importlib import import_module

import pytest
from config import configs
from name import app_name
from peewee_migrate import Router
from pytest_factoryboy import register

from .factories import AdminFactory, RoleFactory, UserFactory

application = import_module(f'{app_name}')

register(UserFactory)
register(AdminFactory)
register(RoleFactory)


@pytest.fixture
def app():
    flask_app = application.create_app(configs['testing'])
    router = Router(flask_app.db.database)
    router.run()
    yield flask_app
    flask_app.db.close_db('')
    current_path = os.path.dirname(__file__)
    os.remove('{}/../test.db'.format(current_path))
