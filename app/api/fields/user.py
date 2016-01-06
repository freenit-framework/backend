from flask_restplus.fields import String, Nested, Integer, Boolean, DateTime
from .. import api
from .role import fields as role_fields


fields = api.model(
    'User', {
        'active': Boolean(),
        'admin': Boolean(),
        'confirmed_at': DateTime(),
        'email': String(
            description='The email',
            required=True,
            default='admin@example.com'
        ),
        'id': Integer(),
        'username': String(
            description='Username',
            required=True,
            default='admin'
        ),
    }
)
