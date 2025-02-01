from .base import BaseRole, ormar_config, make_optional

class Role(BaseRole):
    ormar_config = ormar_config.copy()


class RoleOptional(BaseRole.get_pydantic()):
    pass


make_optional(RoleOptional)
