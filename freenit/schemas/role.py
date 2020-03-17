from marshmallow import fields

from ..fields.objectid import ID
from .base import BaseSchema


class RoleBaseSchema(BaseSchema):
    description = fields.String(description='Description')
    name = fields.String(description='Name')


class BaseRoleSchema(RoleBaseSchema):
    users = fields.List(fields.Nested('UserSchema'), dump_only=True)


class UserRolesSchema(BaseSchema):
    role = fields.Nested('RoleSchema')


class UserAssignSchema(BaseSchema):
    id = ID(description='ID')
