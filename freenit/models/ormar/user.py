import ormar

from freenit.auth import verify
from freenit.config import getConfig
from freenit.models.metaclass import AllOptional
from freenit.models.ormar.base import OrmarBaseModel, OrmarUserMixin
from freenit.models.role import Role

config = getConfig()


class User(OrmarBaseModel, OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    roles = ormar.ManyToMany(Role, unique=True)

    def check(self, password: str) -> bool:
        return verify(password, self.password)


class UserOptional(User, metaclass=AllOptional):
    pass
