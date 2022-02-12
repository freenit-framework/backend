from logging.config import fileConfig

import freenit.app
from alembic import context

from .models import *

fileConfig(context.config.config_file_name)


def run_migrations_offline(config):
    context.configure(
        url=config.dburl,
        target_metadata=config.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        user_module_prefix="sa.",
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online(config):
    connectable = config.engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=config.metadata,
            user_module_prefix="sa.",
        )
        with context.begin_transaction():
            context.run_migrations()
