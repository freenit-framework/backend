from flask_jwt_extended import get_jwt_identity
from flask_rest_api import Blueprint, abort
from flask_security.utils import hash_password

from ..models.auth import User
from ..schemas.auth import UserSchema
from .methodviews import ProtectedMethodView

blueprint = Blueprint('me', 'me')


@blueprint.route('', endpoint='me')
class MeAPI(ProtectedMethodView):
    @blueprint.response(UserSchema)
    def get(self):
        """Get user details"""
        try:
            user = User.get(email=get_jwt_identity())
        except User.DoesNotExist:
            abort(404, message='User not found')
        return user

    @blueprint.arguments(UserSchema(partial=True))
    @blueprint.response(UserSchema)
    def patch(self, args):
        try:
            user = User.get(email=get_jwt_identity())
        except User.DoesNotExist:
            abort(404, message='User not found')
        for field in args:
            setattr(user, field, args[field])
        if 'password' in args:
            user.password = hash_password(user.password)
        user.save()
        return user
