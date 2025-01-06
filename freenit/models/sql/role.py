from .base import OrmarBaseModel, OrmarRoleMixin, make_optional, ormar_config


class Role(OrmarBaseModel, OrmarRoleMixin):
    ormar_config = ormar_config.copy()


class RoleOptional(Role):
    pass


make_optional(RoleOptional)
