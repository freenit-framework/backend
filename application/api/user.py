from flask import current_app
from flask_restplus import abort
from .resources import ProtectedResource
from .namespaces import ns_user
from .schemas import UserSchema
from ..models.auth import User


@ns_user.route('', endpoint='users')
class UserListAPI(ProtectedResource):
    def get(self):
        """List users"""
        schema = UserSchema(many=True)
        response, errors = schema.dump(User.select())
        if errors:
            abort(409, errors)
        return response

    @ns_user.expect(UserSchema.fields())
    def post(self):
        schema = UserSchema()
        user, errors = schema.load(current_app.api.payload)
        if errors:
            abort(409, errors)
        user.save()
        return schema.dump(user)


@ns_user.route('/<id>', endpoint='user')
@ns_user.response(404, 'User not found')
class UserAPI(ProtectedResource):
    def get(self, id):
        """Get user details"""
        try:
            user = User.get(id=id)
        except User.DoesNotExist:
            abort(404, 'User not found')
        schema = UserSchema()
        response, errors = schema.dump(user)
        if errors:
            abort(409, errors)
        return response
