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
    return flask_app
