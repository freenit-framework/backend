from freenit.base_config import Auth, Mail, BaseConfig as FreenitBaseConfig


class BaseConfig(FreenitBaseConfig):
    name = "NAME"
    version = "0.0.1"
    # Modules are inherited from FreenitBaseConfig (default: ["auth"]).
    # Add feature modules here, e.g.:
    # modules = ["auth", "project"]
    stalwart_url = "http://stalwart.example.com"
    stalwart_admin = "%admin"
    stalwart_admin_pass = ""  # nosec: B105


class DevConfig(BaseConfig):
    debug = True
    auth = Auth(False)
    dburl = "sqlite:///db.sqlite"


class TestConfig(BaseConfig):
    debug = True
    auth = Auth(False)
    dburl = "sqlite:///test.sqlite"


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET"  # nosec
    mail = Mail()
