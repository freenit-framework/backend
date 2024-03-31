from ..metaclass import AllOptional
from .base import OrmarBaseModel, OrmarRoleMixin, ormar_config


class Role(OrmarBaseModel, OrmarRoleMixin):
    ormar_config = ormar_config.copy()


class RoleOptional(Role, metaclass=AllOptional):
    ormar_config = ormar_config.copy()
