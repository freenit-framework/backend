from math import ceil

from marshmallow import fields

from .base import BaseSchema


def paginate(query, pagination):
    page = pagination.get('Page', 0)
    per_page = pagination.get('PerPage', 10)
    offset = page * per_page
    total = query.count()
    totalPages = ceil(total / float(per_page))
    data = query.limit(per_page).offset(offset)
    return {
        'data': data,
        'pages': totalPages,
        'total': total,
    }


class PageInSchema(BaseSchema):
    Page = fields.Int()
    PerPage = fields.Int()


def PageOutSchema(schema):
    class PS(BaseSchema):
        pages = fields.Integer()
        total = fields.Integer()
        data = fields.List(
            fields.Nested(schema),
            many=True,
        )

    return PS
