import sys

from marshmallow import fields

from .base import BaseSchema
from .paging import PageOutSchema


class RoleBaseSchema(BaseSchema):
    id = fields.Integer(description='ID', dump_only=True)
    description = fields.String(description='Description')
    name = fields.String(description='Name')


class RoleSchema(RoleBaseSchema):
    users = fields.List(fields.Nested('UserSchema'), dump_only=True)


class UserRolesSchema(BaseSchema):
    role = fields.Nested(RoleSchema)


class UserAssignSchema(BaseSchema):
    id = fields.Integer(description='ID')


PageOutSchema(RoleSchema, sys.modules[__name__])
