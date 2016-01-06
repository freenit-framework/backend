from flask_restplus.fields import String
from .. import api


fields = api.model(
    'Auth', {
        'email': String(
            description='The email',
            required=True,
            default='admin@example.com'
        ),
        'password': String(
            description='The password',
            required=True,
            default='Sekrit'
        ),
    }
)

token_response = api.model(
    'Token', {
        'token': String(),
    }
)
