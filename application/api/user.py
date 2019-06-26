from flask_rest_api import Blueprint, abort

from ..models.auth import User
from ..schemas.auth import UserSchema
from ..schemas.paging import PageInSchema, PageOutSchema, paginate
from .methodviews import ProtectedMethodView

blueprint = Blueprint('user', 'user')


@blueprint.route('/', endpoint='users')
class UserListAPI(ProtectedMethodView):
    @blueprint.arguments(PageInSchema(), location='headers')
    @blueprint.response(PageOutSchema(UserSchema))
    def get(self, pagination):
        """List users"""
        return paginate(User.select(), pagination)

    @blueprint.arguments(UserSchema)
    @blueprint.response(UserSchema)
    def post(self, args):
        """Create user"""
        user = User(**args)
        user.save()
        return user


@blueprint.route('/<user_id>', endpoint='user')
class UserAPI(ProtectedMethodView):
    @blueprint.response(UserSchema)
    def get(self, user_id):
        """Get user details"""
        try:
            user = User.get(id=user_id)
        except User.DoesNotExist:
            abort(404, 'User not found')
        return user
