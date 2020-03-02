import os
from importlib import import_module

from freenit import create_app
from peewee_migrate import Router
from peewee_migrate.router import DEFAULT_MIGRATE_DIR

import pytest
from config import configs
from name import app_name
from pytest_factoryboy import register

from .factories import AdminFactory, RoleFactory, UserFactory

register(UserFactory)
register(AdminFactory)
register(RoleFactory)

schemas = {
    'user': f'{app_name}.schemas.user',
}


@pytest.fixture
def app():
    api = import_module(f'{app_name}.api')
    config = configs['testing']
    flask_app = create_app(config, schemas=schemas)
    api.create_api(flask_app)
    router = Router(
        flask_app.db.database,
        migrate_dir=f'{DEFAULT_MIGRATE_DIR}/main',
    )
    #  log_router = Router(
    #      flask_app.logdb.database,
    #      migrate_dir=f'{DEFAULT_MIGRATE_DIR}/logs',
    #  )
    router.run()
    #  log_router.run()
    yield flask_app
    flask_app.db.close_db('')
    #  flask_app.logdb.close_db('')
    current_path = os.path.dirname(__file__)
    os.remove('{}/../test.db'.format(current_path))
    #  os.remove('{}/../log_test.db'.format(current_path))
