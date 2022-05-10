import socket
from importlib import import_module

import databases
import sqlalchemy

second = 1
minute = 60 * second
hour = 60 * minute
day = 24 * hour
year = 365 * day


class Auth:
    def __init__(self, secure=True, expire=hour, refresh_expire=year):
        self.secure = secure
        self.expire = expire
        self.refresh_expire = refresh_expire


class BaseConfig:
    name = "App Name"
    version = "0.0.1"
    api_root = "/api/v1"
    hostname = socket.gethostname()
    port = 5000
    debug = False
    metadata = sqlalchemy.MetaData()
    dburl = "sqlite:///db.sqlite"
    database = None
    engine = None
    secret = "SECRET"
    user = "freenit.models.ormar"
    meta = None
    auth = Auth()

    def __init__(self):
        self.database = databases.Database(self.dburl)
        self.engine = sqlalchemy.create_engine(self.dburl)

        class Meta:
            database = self.database
            metadata = self.metadata

        self.meta = Meta

    def __repr__(self):
        return (
            f"<{self.envname()} config: {self.name}({self.version}) on {self.hostname}>"
        )

    def get_user(self):
        return import_module(self.user)

    @classmethod
    def envname(cls):
        classname = cls.__name__.lower()
        if classname.endswith("config"):
            return classname[: -len("config")]
        return classname


class DevConfig(BaseConfig):
    debug = True
    dburl = "sqlite:///db.sqlite"
    auth = Auth(False)


class TestConfig(BaseConfig):
    debug = True
    dburl = "sqlite:///test.sqlite"
    auth = Auth(False)


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET"
