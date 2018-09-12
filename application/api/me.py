from flask_restplus import abort
from flask_jwt_extended import get_jwt_identity
from .resources import ProtectedResource
from .namespaces import ns_me
from .schemas import UserSchema
from ..models.auth import User


@ns_me.route('', endpoint='me')
@ns_me.response(404, 'User not found')
class MeAPI(ProtectedResource):
    def get(self):
        """Get my details"""
        email = get_jwt_identity()
        try:
            user = User.get(email=email)
        except User.DoesNotExist:
            abort(404, 'User not found')
        schema = UserSchema()
        response, errors = schema.dump(user)
        if errors:
            abort(409, errors)
        return response
