import ormar
from passlib.hash import pbkdf2_sha256

from ..config import getConfig
from .metaclass import AllOptional
from .ormar import OrmarUserMixin

config = getConfig()


class User(ormar.Model, OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    def check(self, password: str) -> bool:
        config = getConfig()
        result = pbkdf2_sha256.verify(f"{config.secret}{password}", self.password)
        return result


class UserOptional(User, metaclass=AllOptional):
    pass
