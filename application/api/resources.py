from flask_jwt_extended import jwt_required
from flask_restplus import Resource


class ProtectedResource(Resource):
    """
    Resource protedted by jwt
    """
    method_decorators = [jwt_required]
