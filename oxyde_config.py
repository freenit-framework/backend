import os
from pathlib import Path

from oxyde.migrations.utils import detect_dialect

from freenit.config import getConfig
from freenit.modules import get_models


def database_url():
    env = os.getenv("FREENIT_ENV", "prod")
    candidates = [
        os.getenv("FREENIT_DBURL"),
        os.getenv("DATABASE_URL"),
        os.getenv(f"FREENIT_{env.upper()}_DBURL"),
    ]
    for candidate in candidates:
        if candidate:
            return candidate
    if env == "prod":
        raise RuntimeError(
            "No database URL configured. Set FREENIT_DBURL, DATABASE_URL, "
            "or FREENIT_PROD_DBURL."
        )
    filename = "test.sqlite" if env == "test" else "db.sqlite"
    return f"sqlite:///{Path(filename).resolve()}"


def database_dialect():
    explicit = os.getenv("FREENIT_DIALECT")
    if explicit:
        return explicit
    return detect_dialect(database_url())


config = getConfig()
MODELS = get_models(config.modules)
DIALECT = database_dialect()
MIGRATIONS_DIR = "migrations"
DATABASES = {
    "default": database_url(),
}
