from marshmallow import fields

from .base import BaseSchema


class RoleBaseSchema(BaseSchema):
    id = fields.Integer(description='ID', dump_only=True)
    description = fields.String(description='Description')
    name = fields.String(description='Name')


class BaseRoleSchema(RoleBaseSchema):
    users = fields.List(fields.Nested('UserSchema'), dump_only=True)


class UserRolesSchema(BaseSchema):
    role = fields.Nested('RoleSchema')


class UserAssignSchema(BaseSchema):
    id = fields.Integer(description='ID')
