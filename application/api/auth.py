from datetime import datetime

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies
)
from flask_restplus import Resource, abort
from flask_security.utils import verify_password

from ..models.auth import User
from .namespaces import ns_auth
from .schemas import TokenSchema


@ns_auth.route('/login', endpoint='auth_login')
class AuthLoginAPI(Resource):
    @ns_auth.response(401, 'Invalid credentials')
    @ns_auth.expect(TokenSchema.fields())
    def post(self):
        """Authenticates and generates a token"""
        schema = TokenSchema()
        data, errors = schema.load(current_app.api.payload)
        if errors:
            return errors, 400
        try:
            user = User.get(email=data.email)
        except User.DoesNotExist:
            abort(403, 'No such user, or wrong password')
        if not user or not user.active:
            abort(403, 'No such user, or wrong password')
        if not verify_password(data.password, user.password):
            abort(403, 'No such user, or wrong password')
        access_token = create_access_token(identity=user.email)
        refresh_token = create_refresh_token(identity=user.email)
        access_expire = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        refresh_expire = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        resp = jsonify(
            {
                'access': access_token,
                'refresh': refresh_token,
                'accessExpire': int(access_expire.total_seconds()),
                'refreshExpire': int(refresh_expire.total_seconds()),
            }
        )
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        refresh_path = current_app.config['JWT_REFRESH_COOKIE_PATH']
        refresh_secure = current_app.config['JWT_COOKIE_SECURE']
        refresh_expire_date = datetime.now() + refresh_expire
        resp.set_cookie(
            'refresh_expire',
            value=str(refresh_expire_date),
            expires=refresh_expire_date,
            path=refresh_path,
            httponly=True,
            secure=refresh_secure,
        )
        return resp


@ns_auth.route('/logout', endpoint='auth_logout')
class AuthLogoutAPI(Resource):
    def post(self):
        """Logout"""
        resp = jsonify({'logout': True})
        unset_jwt_cookies(resp)
        return resp


@ns_auth.route('/refresh', endpoint='auth_refresh')
class AuthRefreshAPI(Resource):
    @jwt_refresh_token_required
    def post(self):
        """Refresh access token"""
        email = get_jwt_identity()
        try:
            user = User.get(email=email)
        except User.DoesNotExist:
            abort(403, 'No such user, or wrong password')
        access_expire = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        access_token = create_access_token(identity=user.email)
        refresh_expire_date = datetime.strptime(
            request.cookies['refresh_expire'],
            '%Y-%m-%d %H:%M:%S.%f'
        )
        refresh_delta = refresh_expire_date - datetime.now()
        resp = jsonify(
            {
                'access': access_token,
                'accessExpire': int(access_expire.total_seconds()),
                'refreshExpire': int(refresh_delta.total_seconds()),
            }
        )
        set_access_cookies(resp, access_token)
        return resp
