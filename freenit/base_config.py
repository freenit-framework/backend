import socket
import sqlalchemy
import databases
from importlib import import_module


class Auth:
    def __init__(self, secure = True, expire = 3600, refresh_expire = 7200):
        self.secure = secure
        self.expire = expire
        self.refresh_expire = refresh_expire


class BaseConfig:
    name = "App Name"
    version = "0.0.1"
    hostname = socket.gethostname()
    port = 5000
    debug = False
    metadata = sqlalchemy.MetaData()
    dburl = "sqlite:///db.sqlite"
    database = None
    engine = None
    secret = "SECRET"
    user = 'freenit.models.user'
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
        if classname.endswith('config'):
            return classname[:-len('config')]
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
