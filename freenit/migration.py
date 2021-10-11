from logging.config import fileConfig
from .models import *

from alembic import context
from freenit.config import getConfig
import freenit.app

config = getConfig()
fileConfig(context.config.config_file_name)


def run_migrations_offline():
    context.configure(
        url=config.dburl,
        target_metadata=config.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        user_module_prefix="sa.",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = config.engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=config.metadata,
            user_module_prefix="sa.",
        )
        with context.begin_transaction():
            context.run_migrations()
