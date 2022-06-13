import ormar

from freenit.config import getConfig
from freenit.models.user import User

from ..metaclass import AllOptional
from .base import OrmarBaseModel, OrmarGroupMixin

config = getConfig()


class Group(OrmarBaseModel, OrmarGroupMixin):
    class Meta(config.meta):
        tablename = "groups"


class GroupOptional(Group, metaclass=AllOptional):
    pass


class GroupUser(OrmarBaseModel):
    class Meta(config.meta):
        constraints = [ormar.UniqueColumns("user", "group")]

    id = ormar.Integer(primary_key=True)
    user = ormar.ForeignKey(User)
    group = ormar.ForeignKey(Group)
