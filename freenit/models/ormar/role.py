from freenit.config import getConfig

from ..metaclass import AllOptional
from .base import OrmarBaseModel, OrmarRoleMixin

config = getConfig()


class Role(OrmarBaseModel, OrmarRoleMixin):
    class Meta(config.meta):
        pass


class RoleOptional(Role, metaclass=AllOptional):
    pass
