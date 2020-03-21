import os

import pytest
from peewee_migrate import Router
from peewee_migrate.router import DEFAULT_MIGRATE_DIR
from pytest_factoryboy import register

from config import configs
from freenit import create_app

from .factories import AdminFactory, RoleFactory, UserFactory

register(UserFactory)
register(AdminFactory)
register(RoleFactory)


@pytest.fixture
def app():
    dbtype = os.environ.get('DBTYPE', 'sql')
    config = configs['testing']
    flask_app = create_app(config, dbtype=dbtype)
    if dbtype == 'sql':
        router = Router(
            flask_app.db.database,
            migrate_dir=f'{DEFAULT_MIGRATE_DIR}/main',
        )
        router.run()
    yield flask_app
    if dbtype == 'sql':
        flask_app.db.close_db('')
        current_path = os.path.dirname(__file__)
        os.remove('{}/../test.db'.format(current_path))
