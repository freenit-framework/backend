from marshmallow import Schema, fields, post_load
from ..models.parsing import TokenModel


class TokenSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

    @post_load
    def make_object(self, data):
        return TokenModel(**data)
