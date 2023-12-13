from freenit.base_config import Auth
from freenit.base_config import BaseConfig as FreenitBaseConfig


class BaseConfig(FreenitBaseConfig):
    name = "NAME"
    version = "0.0.1"


class DevConfig(BaseConfig):
    debug = True
    auth = Auth(False)
    dburl = "sqlite:///db.sqlite"


class TestConfig(BaseConfig):
    debug = True
    auth = Auth(False)
    dburl = "sqlite:///test.sqlite"


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET" #nosec
