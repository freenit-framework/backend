from pydantic import Field

from freenit.models.ldap.base import LDAPBaseModel, LDAPUserMixin


class UserSafe(LDAPBaseModel, LDAPUserMixin):
    pass


class User(UserSafe):
    password: str = Field("", description=("Password"))


class UserOptional(User):
    pass


UserOptionalPydantic = UserOptional
