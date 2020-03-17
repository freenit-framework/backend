from marshmallow import fields

from .base import BaseSchema
from .role import UserRolesSchema


class TokenSchema(BaseSchema):
    email = fields.Email(required=True, description='Email')
    password = fields.Str(required=True, description='Password')


class BaseUserSchema(BaseSchema):
    active = fields.Boolean(description='Activate the user')
    admin = fields.Boolean(description='Is the user admin?')
    email = fields.Email(required=True, description='Email')
    password = fields.Str(
        required=True,
        description='Password',
        load_only=True
    )
    roles = fields.List(
        fields.Nested(UserRolesSchema),
        many=True,
        dump_only=True,
    )
    confirmed_at = fields.DateTime(
        description='Time when user was confirmed',
        dump_only=True,
    )


class RefreshSchema(BaseSchema):
    access = fields.Str()
    accessExpire = fields.Integer()
    refreshExpire = fields.Integer()


class LoginSchema(RefreshSchema):
    refresh = fields.Str()


class ResetSchema(BaseSchema):
    token = fields.String(required=True)
    password = fields.String(required=True)
