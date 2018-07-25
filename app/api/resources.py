from flask_restplus import Resource, fields
from flask_jwt import jwt_required
from . import api


fields = api.model(
    'JWTFields',
    {
        'jwt': fields.String(),
    },
)


class ProtectedResource(Resource):
    """
    Resource protedted by jwt
    """
    method_decorators = [jwt_required()]
