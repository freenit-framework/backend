import os
import re
from .resources import ProtectedResource
from .namespaces import ns_user
from .fields.user import fields
from ..models.auth import User


@ns_user.route('', endpoint='users')
class UserListAPI(ProtectedResource):
    @ns_user.marshal_with(fields)
    def get(self):
        """List users"""
        return [user for user in User.select()]


@ns_user.route('/<id>', endpoint='user')
@ns_user.response(404, 'User not found')
class UserAPI(ProtectedResource):
    @ns_user.marshal_with(fields)
    def get(self, id):
        """Get user details"""
        try:
            user = User.get(id=id)
        except User.DoesNotExist:
            abort(404, 'User not found')
        return user
