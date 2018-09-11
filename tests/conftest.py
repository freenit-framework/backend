import os
import pytest
from application import create_app
from config import configs
from peewee_migrate import Router
from pytest_factoryboy import register
from .factories import UserFactory, AdminFactory, RoleFactory


register(UserFactory)
register(AdminFactory)
register(RoleFactory)


@pytest.fixture
def app():
    flask_app = create_app(configs['testing'])
    router = Router(flask_app.db.database)
    router.run()
    yield flask_app
    flask_app.db.close_db('')
    current_path = os.path.dirname(__file__)
    os.remove('{}/../test.db'.format(current_path))
