import socket
import sqlalchemy
import databases
from importlib import import_module


class BaseConfig:
    name = "App Name"
    version = "0.0.1"
    envname = "base"
    hostname = socket.gethostname()
    port = 5000
    debug = False
    envname = "prod"
    metadata = sqlalchemy.MetaData()
    dburl = "sqlite:///db.sqlite"
    database = None
    engine = None
    secret = "SECRET"
    cookie_secure = True
    user = 'freenit.models.user'

    def __init__(self):
        self.database = databases.Database(self.dburl)
        self.engine = sqlalchemy.create_engine(self.dburl)

    def __repr__(self):
        return (
            f"<{self.envname} config: {self.name}({self.version}) on {self.hostname}>"
        )

    def get_user(self):
        return import_module(self.user)


class DevConfig(BaseConfig):
    envname = "dev"
    debug = True
    cookie_secure = False
    dburl = "sqlite:///db.sqlite"


class TestConfig(BaseConfig):
    envname = "test"
    debug = True
    cookie_secure = False
    dburl = "sqlite:///test.sqlite"


class ProdConfig(BaseConfig):
    envname = "prod"
    secret = "MORESECURESECRET"
