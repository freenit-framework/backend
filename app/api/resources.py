from flask_restplus import Resource
from flask_jwt import jwt_required
from . import api


class ProtectedResource(Resource):
    """
    Resource protedted by jwt
    """
    method_decorators = [jwt_required()]
