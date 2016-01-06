from flask_restplus.fields import String
from .. import api


fields = api.model(
    'Roles', {
        'name': String(required=True),
        'description': String(required=True),
    }
)
