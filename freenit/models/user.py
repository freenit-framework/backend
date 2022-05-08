import ormar
from passlib.hash import pbkdf2_sha256

from ..config import getConfig
from .base import UserMixin
from .ormar import OrmarUserMixin

config = getConfig()


class User(ormar.Model, UserMixin, OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    def __init__(self, *args, **kwargs):
        ormar.Model.__init__(self, *args, **kwargs)
        email = kwargs.get("email", "")
        password = kwargs.get("password", "")
        active = kwargs.get("active", False)
        UserMixin.__init__(self, email, password, active)

    def __setattr__(self, name: str, value) -> None:
        UserMixin.__setattr__(self, name, value)
