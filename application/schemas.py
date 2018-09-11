from marshmallow import Schema, fields, post_load
from flask_restplus import fields as rest_fields
from .models.auth import User
from .models.parsing import TokenModel
from flask_restplus.model import Model


def marshmallowToField(field):
    if type(field) in [fields.Email, fields.String]:
        return rest_fields.String
    if type(field) in [fields.Bool, fields.Boolean]:
        return rest_fields.Boolean
    if type(field) in [fields.Int, fields.Integer]:
        return rest_fields.Integer
    if type(field) == fields.DateTime:
        return rest_fields.DateTime
    else:
        raise ValueError('Unknown field of type {}'.format(type(field)))


class BaseSchema(Schema):
    @post_load
    def make_object(self, data):
        return self.Meta.model(**data)

    @classmethod
    def fields(cls, required=None):
        marshal_fields = {}
        for name in cls._declared_fields.keys():
            field = cls._declared_fields[name]
            if field.dump_only:
                continue
            fieldType = marshmallowToField(field)
            description = field.metadata.get('description', None)
            if required is None:
                field_required = field.required
            else:
                field_required = required
            marshal_fields[name] = fieldType(
                description=description,
                required=required,
            )
        return Model(cls.Meta.name, marshal_fields)


class TokenSchema(BaseSchema):
    email = fields.Email(required=True, description='Email')
    password = fields.Str(required=True, description='Password')

    class Meta:
        model = TokenModel
        name = 'Token'


class UserSchema(BaseSchema):
    id = fields.Integer(description='ID', dump_only=True)
    email = fields.Email(required=True, description='Email')
    password = fields.Str(required=True, description='Password', load_only=True)
    active = fields.Boolean(default=True)
    admin = fields.Boolean(default=False)
    confirmed_at = fields.DateTime()

    class Meta:
        model = User
        name = 'User'
