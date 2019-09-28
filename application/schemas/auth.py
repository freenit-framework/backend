from marshmallow import fields

from .base import BaseSchema


class UserAssignSchema(BaseSchema):
    id = fields.Integer(description='ID')


class TokenSchema(BaseSchema):
    email = fields.Email(required=True, description='Email')
    password = fields.Str(required=True, description='Password')


class RoleBaseSchema(BaseSchema):
    id = fields.Integer(description='ID', dump_only=True)
    description = fields.String(description='Description')
    name = fields.String(description='Name')


class RoleSchema(RoleBaseSchema):
    users = fields.List(fields.Nested('UserSchema'), dump_only=True)


class UserRolesSchema(BaseSchema):
    role = fields.Nested(RoleSchema)


class UserSchema(BaseSchema):
    id = fields.Integer(description='ID', dump_only=True)
    active = fields.Boolean(description='Activate the user', default=True)
    admin = fields.Boolean(description='Is the user admin?', default=False)
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
