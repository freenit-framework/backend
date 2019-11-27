from flask_security.utils import hash_password
from flask_smorest import Blueprint, abort

from ..models.user import User
from ..schemas.paging import PageInSchema, paginate
from ..schemas.user import UserPageOutSchema, UserSchema
from .methodviews import ProtectedMethodView

blueprint = Blueprint('users', 'user')


@blueprint.route('', endpoint='list')
class UserListAPI(ProtectedMethodView):
    @blueprint.arguments(PageInSchema(), location='headers')
    @blueprint.response(UserPageOutSchema)
    def get(self, pagination):
        """List users"""
        return paginate(User.select(), pagination)

    @blueprint.arguments(UserSchema)
    @blueprint.response(UserSchema)
    def post(self, args):
        """Create user"""
        user = User(**args)
        user.password = hash_password(user.password)
        user.save()
        return user


@blueprint.route('/<user_id>', endpoint='detail')
class UserAPI(ProtectedMethodView):
    @blueprint.response(UserSchema)
    def get(self, user_id):
        """Get user details"""
        try:
            user = User.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='User not found')
        return user

    @blueprint.arguments(UserSchema(partial=True))
    @blueprint.response(UserSchema)
    def patch(self, args, user_id):
        try:
            user = User.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='User not found')
        for field in args:
            setattr(user, field, args[field])
        if 'password' in args:
            user.password = hash_password(user.password)
        user.save()
        return user

    @blueprint.response(UserSchema)
    def delete(self, user_id):
        try:
            user = User.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='User not found')
        user.delete_instance()
        return user
