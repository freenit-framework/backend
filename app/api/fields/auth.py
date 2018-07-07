from flask_restplus.fields import String
from .. import api


forgot_password_fields = api.model(
    'ForgotPassword',
    {
        'email': String(
            description='The email',
            required=True,
        ),
    },
)


token_fields = api.clone(
    'Auth',
    forgot_password_fields,
    {
        'password': String(
            description='The password',
            required=True,
            default='Sekrit'
        ),
    },
)
