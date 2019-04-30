from flask_rest_api import Blueprint

from ..models.auth import User
from .methodviews import ProtectedMethodView
from .schemas import UserSchema

user = Blueprint('user', 'user')


@user.route('/', endpoint='users')
class UserListAPI(ProtectedMethodView):
    @user.response(UserSchema(many=True))
    def get(self):
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
        user = User(**data)
        user.save()
        return user


@user.route('/<id>', endpoint='user')
class UserAPI(ProtectedMethodView):
    @user.response(UserSchema)
    def get(self, id):
        """Get user details"""
        try:
            user = User.get(id=id)
        except User.DoesNotExist:
            return {'message': 'User not found'}, 404
        return user
