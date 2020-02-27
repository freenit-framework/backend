from flask import current_app
from flask_jwt_extended import get_jwt_identity
from flask_security.utils import hash_password
from flask_smorest import Blueprint, abort

from ..schemas.user import UserSchema
from .methodviews import ProtectedMethodView

blueprint = Blueprint('profile', 'profile')


@blueprint.route('', endpoint='profile')
class ProfileAPI(ProtectedMethodView):
    @blueprint.response(UserSchema)
    def get(self):
        """Get user details"""
        User = current_app.user_datastore.user_model
        try:
            user = User.get(id=get_jwt_identity())
        except User.DoesNotExist:
            abort(404, message='User not found')
        return user

    @blueprint.arguments(UserSchema(partial=True))
    @blueprint.response(UserSchema)
    def patch(self, args):
        """Edit user details"""
        User = current_app.user_datastore.user_model
        try:
            user = User.get(id=get_jwt_identity())
        except User.DoesNotExist:
            abort(404, message='User not found')
        for field in args:
            setattr(user, field, args[field])
        if 'password' in args:
            user.password = hash_password(user.password)
        user.save()
        return user
