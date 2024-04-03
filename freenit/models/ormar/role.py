from .base import OrmarBaseModel, OrmarRoleMixin, ormar_config


class Role(OrmarBaseModel, OrmarRoleMixin):
    ormar_config = ormar_config.copy()


class RoleOptional(Role):
    pass

for field_name in RoleOptional.model_fields:
    RoleOptional.model_fields[field_name].default = None
