from .base import OrmarBaseModel, OrmarRoleMixin, generate_optional, ormar_config


class Role(OrmarBaseModel, OrmarRoleMixin):
    ormar_config = ormar_config.copy()


RoleOptional = generate_optional(Role)
