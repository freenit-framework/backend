from flask_restplus import Resource, abort
from flask_jwt_extended import jwt_required


class ProtectedResource(Resource):
    """
    Resource protedted by jwt
    """
    method_decorators = [jwt_required]
