from math import ceil

from flask_smorest import abort
from marshmallow import fields

from .base import BaseSchema


def paginate(query, pagination):
    page = pagination.get('Page', 0)
    per_page = pagination.get('PerPage', 10)
    offset = page * per_page
    total = query.count()
    if offset > total:
        abort(409, message='Requested range out of boundaries')
    totalPages = ceil(total / float(per_page))
    data = []
    if getattr(query, '__sql__', None):
        data = query.limit(per_page).offset(offset)
    else:
        end = offset + per_page
        data = query[offset:end]
    return {
        'data': data,
        'pages': totalPages,
        'total': total,
    }


class PageInSchema(BaseSchema):
    Page = fields.Int()
    PerPage = fields.Int()


def PageOutSchema(schema, module):
    name = schema.__name__
    if name.endswith("Schema"):
        name = name[:-6] or name
    name += 'PageOutSchema'

    base = (schema, )
    PS = type(
        name,
        base,
        {
            'pages': fields.Integer(),
            'total': fields.Integer(),
            'data': fields.List(fields.Nested(schema)),
        }
    )
    setattr(module, name, PS)
    return PS
