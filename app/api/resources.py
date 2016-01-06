from flask_restplus import Resource
from flask_jwt import jwt_required


class ProtectedResource(Resource):
    """
    Resource protedted by jwt
    """
    method_decorators = [jwt_required()]
