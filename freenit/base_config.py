import socket
from importlib import import_module

import databases
import sqlalchemy

second = 1
minute = 60 * second
hour = 60 * minute
day = 24 * hour
year = 365 * day
register_message = """Hello,

Please confirm user registration by following this link

{}

Regards,
Freenit
"""


class Auth:
    def __init__(self, secure=True, expire=hour, refresh_expire=year) -> None:
        self.secure = secure
        self.expire = expire
        self.refresh_expire = refresh_expire


class Mail:
    def __init__(
        self,
        server="mail.example.com",
        user="user@example.com",
        password="Sekrit",  # nosec
        port=587,
        tls=True,
        from_addr="no-reply@mail.com",
        register_subject="[Freenit] User Registration",
        register_message=register_message,
        master_user="dovecot@example.com",
        master_pw="Sekrit",
    ) -> None:
        self.server = server
        self.user = user
        self.password = password
        self.port = port
        self.tls = tls
        self.from_addr = from_addr
        self.register_subject = register_subject
        self.register_message = register_message
        self.master_user = master_user
        self.master_pw = master_pw


class LDAP:
    def __init__(
        self,
        host="ldap.example.com",
        tls=True,
        base="uid={},ou={},dc=account,dc=ldap",
        service_dn="cn=freenit,dc=service,dc=ldap",
        service_pw="",
        userClasses=["pilotPerson", "posixAccount"],
        groupClasses=["groupOfUniqueNames"],
    ):
        self.host = host
        self.tls = tls
        self.base = base
        self.service_dn = service_dn
        self.service_pw = service_pw
        self.userClasses = userClasses
        self.groupClasses = groupClasses


class BaseConfig:
    name = "Freenit"
    version = "0.0.1"
    api_root = "/api/v1"
    hostname = socket.gethostname()
    port = 5000
    debug = False
    metadata = sqlalchemy.MetaData()
    dburl = "sqlite:///db.sqlite"
    database = None
    engine = None
    secret = "SECRET"  # nosec
    user = "freenit.models.sql.user"
    role = "freenit.models.sql.role"
    theme = "freenit.models.sql.theme"
    theme_name = "Freenit"
    meta = None
    auth = Auth()
    mail = Mail()
    ldap = LDAP()

    def __init__(self):
        self.database = databases.Database(self.dburl)
        self.engine = sqlalchemy.create_engine(self.dburl)

    def __repr__(self):
        return (
            f"<{self.envname()} config: {self.name}({self.version}) on {self.hostname}>"
        )

    def get_model(self, model):
        mymodel = getattr(self, model)
        return import_module(mymodel)

    @classmethod
    def envname(cls):
        classname = cls.__name__.lower()
        if classname.endswith("config"):
            return classname[: -len("config")]
        return classname


class DevConfig(BaseConfig):
    debug = True
    dburl = "sqlite:///db.sqlite"
    auth = Auth(secure=False)
    mail = None


class TestConfig(BaseConfig):
    debug = True
    dburl = "sqlite:///test.sqlite"
    auth = Auth(secure=False)
    mail = None


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET"  # nosec
