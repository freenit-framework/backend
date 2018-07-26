import uuid
from flask_restplus import Resource, abort
from flask import request, current_app
from flask_jwt import _jwt, JWTError
from .namespaces import ns_auth
from ..models.auth import User
from ..schemas import TokenSchema


@ns_auth.route('/tokens', endpoint='auth.token')
class AuthAPI(Resource):
    @ns_auth.response(401, 'Invalid credentials')
    @ns_auth.expect(TokenSchema.fields())
    def post(self):
        """Authenticates and generates a token."""
        schema = TokenSchema()
        data, errors = schema.load(current_app.api.payload)
        if errors:
            return errors, 409
        identity = _jwt.authentication_callback(data.email, data.password)
        if identity is not None:
            user = User.get(id=identity.id)
            if user and user.active:
                access_token = _jwt.jwt_encode_callback(identity)
                return {
                    "token": 'JWT {}'.format(access_token.decode('utf-8')),
                }
        raise JWTError('Bad Request', 'Invalid credentials')
