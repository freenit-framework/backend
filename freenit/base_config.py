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
        service_dn="cn=freenit,dc=service,dc=ldap",
        service_pw="",
        roleDN="cn={}",
        roleBase="dc=group,dc=ldap",
        roleClasses=["groupOfUniqueNames"],
        roleMemberAttr="uniqueMember",
        groupDN="cn={}",
        groupClasses=["posixGroup"],
        userBase="dc=account,dc=ldap",
        userDN="uid={}",
        userClasses=["pilotPerson", "posixAccount"],
        userMemberAttr="memberOf",
        uidNextClass="uidNext",
        uidNextDN="cn=uidnext,dc=ldap",
        uidNextField="uidNumber",
        gidNextClass="gidNext",
        gidNextDN="cn=gidnext,dc=ldap",
        gidNextField="gidNumber",
        domainDN="ou={}",
        domainClasses=["organizationalUnit", "pmiDelegationPath"],
    ):
        self.host = host
        self.tls = tls
        self.service_dn = service_dn
        self.service_pw = service_pw
        self.roleBase = roleBase
        self.roleClasses = roleClasses
        self.roleDN = f"{roleDN},{roleBase}"
        self.roleMemberAttr = roleMemberAttr
        self.groupClasses = groupClasses
        self.groupDN = f"{groupDN},{domainDN},{roleBase}"
        self.userBase = userBase
        self.userDN = f"{userDN},{domainDN},{userBase}"
        self.userClasses = userClasses
        self.userMemberAttr = userMemberAttr
        self.uidNextClass = uidNextClass
        self.uidNextDN = uidNextDN
        self.uidNextField = uidNextField
        self.gidNextClass = gidNextClass
        self.gidNextDN = gidNextDN
        self.gidNextField = gidNextField
        self.domainDN = domainDN
        self.domainClasses = domainClasses


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
    mail = None
    ldap = None

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


class TestConfig(BaseConfig):
    debug = True
    dburl = "sqlite:///test.sqlite"
    auth = Auth(secure=False)


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET"  # nosec
    mail = Mail()
