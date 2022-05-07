import ormar

from ..config import getConfig
from .ormar import OrmarUserMixin

config = getConfig()


class User(OrmarUserMixin):
    class Meta(config.meta):
        tablename = "users"

    id: int = ormar.Integer(primary_key=True)
