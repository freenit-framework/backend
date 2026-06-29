import socket
from importlib import import_module
from pathlib import Path

import oxyde

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


class XMPP:
    def __init__(self, ws_url="") -> None:
        self.ws_url = ws_url


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
        userClasses=["pilotPerson", "posixAccount", "omemoPerson"],
        userMemberAttr="memberOf",
        userOmemoAttr="omemoBundle",
        uidNextClass="uidNext",
        uidNextDN="cn=uidnext,dc=ldap",
        uidNextField="uidNumber",
        gidNextClass="gidNext",
        gidNextDN="cn=gidnext,dc=ldap",
        gidNextField="gidNumber",
        domainDN="ou={}",
        domainClasses=["organizationalUnit", "pmiDelegationPath"],
        mailinglistBase="ou=mailinglists,dc=ldap",
        mailinglistDN="cn={}",
        mailinglistClasses=["freenitMailingList"],
        pendingSubscriberClasses=["freenitPendingSubscriber"],
        moderationMessageClasses=["freenitModerationMessage"],
        mlidNextClass="freenitMailingListIdNext",
        mlidNextDN="cn=mlidnext,dc=ldap",
        mlidNextField="mlidNumber",
        gitBase="ou=git,dc=ldap",
        gitRepoDN="cn={}",
        gitRepoClasses=["freenitGitRepo"],
        gitPermissionClasses=["freenitGitPermission"],
        gitPushLogClasses=["freenitGitPushLog"],
        gitCommitTaskRefClasses=["freenitGitCommitTaskRef"],
        gitIdNextClass="freenitGitIdNext",
        gitIdNextDN="cn=gitidnext,dc=ldap",
        gitIdNextField="gitIdNumber",
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
        self.userOmemoAttr = userOmemoAttr
        self.uidNextClass = uidNextClass
        self.uidNextDN = uidNextDN
        self.uidNextField = uidNextField
        self.gidNextClass = gidNextClass
        self.gidNextDN = gidNextDN
        self.gidNextField = gidNextField
        self.domainDN = domainDN
        self.domainClasses = domainClasses
        self.mailinglistBase = mailinglistBase
        self.mailinglistDN = f"{mailinglistDN},{mailinglistBase}"
        self.mailinglistClasses = mailinglistClasses
        self.pendingSubscriberClasses = pendingSubscriberClasses
        self.moderationMessageClasses = moderationMessageClasses
        self.mlidNextClass = mlidNextClass
        self.mlidNextDN = mlidNextDN
        self.mlidNextField = mlidNextField
        self.gitBase = gitBase
        self.gitRepoDN = f"{gitRepoDN},{gitBase}"
        self.gitRepoClasses = gitRepoClasses
        self.gitPermissionClasses = gitPermissionClasses
        self.gitPushLogClasses = gitPushLogClasses
        self.gitCommitTaskRefClasses = gitCommitTaskRefClasses
        self.gitIdNextClass = gitIdNextClass
        self.gitIdNextDN = gitIdNextDN
        self.gitIdNextField = gitIdNextField


class BaseConfig:
    name = "Freenit"
    version = "0.0.1"
    api_root = "/api/v1"
    hostname = socket.gethostname()
    port = 5000
    debug = False
    dburl = "sqlite:///db.sqlite"
    _database = None
    secret = "SECRET"  # nosec
    user = "freenit.models.sql.user"
    role = "freenit.models.sql.role"
    mailinglist = "freenit.models.sql.mailinglist"
    project = "freenit.models.sql.project"
    lms = "freenit.models.sql.lms"
    git = "freenit.models.sql.git"
    blog = "freenit.models.sql.blog"
    modules = ["auth", "blog"]
    meta = None
    auth = Auth()
    mail = None
    ldap = None
    xmpp = XMPP()
    stalwart_url = "http://stalwart.example.com"
    stalwart_admin = "%admin"
    stalwart_admin_pass = ""  # nosec: B105

    def __init__(self):
        dburl = self.dburl
        if dburl.startswith("sqlite:///") and not dburl.startswith("sqlite:////"):
            dbpath = Path(dburl.removeprefix("sqlite:///")).resolve()
            dburl = f"sqlite:///{dbpath}"
        self.dburl = dburl

    @property
    def database(self):
        if self._database is None:
            self._database = oxyde.AsyncDatabase(self.dburl, overwrite=True)
        return self._database

    @database.setter
    def database(self, value):
        self._database = value

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
    modules = [
        "auth",
        "user",
        "role",
        "project",
        "lms",
        "mailinglist",
        "domain",
        "dav",
        "mail",
        "sieve",
        "chat",
        "omemo",
        "git",
        "blog",
    ]


class ProdConfig(BaseConfig):
    secret = "MORESECURESECRET"  # nosec
    mail = Mail()
