from flask_rest_api import Blueprint

from ..models.auth import User
from ..schemas.auth import UserSchema
from ..schemas.paging import PagingSchema
from .methodviews import ProtectedMethodView

user = Blueprint('user', 'user')


@user.route('/', endpoint='users')
class UserListAPI(ProtectedMethodView):
    @user.arguments(PagingSchema(), location='headers')
    @user.response(UserSchema(many=True))
    def get(self, pagination):
        """List users"""
        return User.select()

    @user.arguments(UserSchema)
    @user.response(UserSchema)
    def post(self, args):
        """Create user"""
        schema = UserSchema()
        data, errors = schema.load(args)
        if errors:
            return errors, 409
        account = User(**data)
        account.save()
        return account


@user.route('/<id>', endpoint='user')
class UserAPI(ProtectedMethodView):
    @user.response(UserSchema)
    def get(self, id):
        """Get user details"""
        try:
            account = User.get(id=id)
        except User.DoesNotExist:
            return {'message': 'User not found'}, 404
        return account
