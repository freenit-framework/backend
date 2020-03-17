from marshmallow import Schema

from ..fields.objectid import ID


class BaseSchema(Schema):
    id = ID(description='ID', dump_only=True)

    class Meta:
        strict = True
        ordered = True
