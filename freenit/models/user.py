from ..auth import verify
from ..config import getConfig
from .metaclass import AllOptional
from .ormar import OrmarBaseModel, OrmarUserMixin

config = getConfig()


class User(OrmarBaseModel, OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    def check(self, password: str) -> bool:
        return verify(password, self.password)


class UserOptional(User, metaclass=AllOptional):
    pass
