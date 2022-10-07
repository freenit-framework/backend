import factory
from passlib.hash import pbkdf2_sha256

from freenit.config import getConfig
from freenit.models.role import Role as RoleModel

config = getConfig()
auth = config.get_model("user")


class User(factory.Factory):
    class Meta:
        model = auth.User

    email = factory.Faker("email")
    password = pbkdf2_sha256.hash(f"{config.secret}Sekrit")
    active = True


class InactiveUser(User):
    active = False


class Role(factory.Factory):
    class Meta:
        model = RoleModel

    name = factory.Faker("pystr")
