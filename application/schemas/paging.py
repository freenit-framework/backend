from marshmallow import fields

from .base import BaseSchema


class PagingSchema(BaseSchema):
    Page = fields.Int()
    PerPage = fields.Int()
