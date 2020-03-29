from flask import current_app
from flask_security.utils import hash_password
from flask_smorest import Blueprint, abort

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
        User = current_app.user_datastore.user_model
        if current_app.dbtype == 'sql':
            return paginate(User.select(), pagination)
        else:
            return paginate(User.objects.all(), pagination)

    @blueprint.arguments(UserSchema)
    @blueprint.response(UserSchema)
    def post(self, args):
        """Create user"""
        User = current_app.user_datastore.user_model
        user = User(**args)
        user.password = hash_password(user.password)
        user.save()
        return user


@blueprint.route('/<user_id>', endpoint='detail')
class UserAPI(ProtectedMethodView):
    @blueprint.response(UserSchema)
    def get(self, user_id):
        """Get user details"""
        User = current_app.user_datastore.user_model
        try:
            if current_app.dbtype == 'sql':
                user = User.get(id=user_id)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='User not found')
        return user

    @blueprint.arguments(UserSchema(partial=True))
    @blueprint.response(UserSchema)
    def patch(self, args, user_id):
        """Edit user details"""
        User = current_app.user_datastore.user_model
        try:
            if current_app.dbtype == 'sql':
                user = User.get(id=user_id)
            else:
                user = User.objects.get(id=user_id)
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
        """Delete user"""
        User = current_app.user_datastore.user_model
        try:
            if current_app.dbtype == 'sql':
                user = User.get(id=user_id)
            else:
                user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            abort(404, message='User not found')
        user.delete_instance()
        return user
