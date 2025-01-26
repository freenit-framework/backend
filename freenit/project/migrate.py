import importlib

from alembic import command
from alembic.config import Config
from name import app_name

alembic_cfg = Config("alembic.ini")


def db_setup():
    importlib.import_module(f"{app_name}.app")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    db_setup()
