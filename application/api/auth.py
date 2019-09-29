from datetime import datetime

from flask import current_app, jsonify, request
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies
)
from flask_rest_api import Blueprint, abort
from flask_security.utils import verify_password, hash_password

from ..models.auth import User
from ..schemas.auth import LoginSchema, RefreshSchema, TokenSchema, UserSchema

blueprint = Blueprint('auth', 'auth')


@blueprint.route('/login', endpoint='auth_login')
class AuthLoginAPI(MethodView):
    @blueprint.response(LoginSchema)
    @blueprint.arguments(TokenSchema)
    def post(self, args):
        """Authenticates and generates a token"""
        email = args.get('email', None)
        password = args.get('password', None)
        if email is None:
            abort(403, message='Email not provided')
        try:
            user = User.get(email=email)
        except User.DoesNotExist:
            abort(403, message='No such user, or wrong password')
        if not user or not user.active:
            abort(403, message='No such user, or wrong password')
        if not verify_password(password, user.password):
            abort(403, message='No such user, or wrong password')
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


@blueprint.route('/logout', endpoint='auth_logout')
class AuthLogoutAPI(MethodView):
    def post(self):
        """Logout"""
        resp = jsonify({})
        unset_jwt_cookies(resp)
        return resp


@blueprint.route('/refresh', endpoint='auth_refresh')
class AuthRefreshAPI(MethodView):
    @blueprint.response(RefreshSchema)
    @jwt_refresh_token_required
    def post(self):
        """Refresh access token"""
        email = get_jwt_identity()
        try:
            user = User.get(email=email)
        except User.DoesNotExist:
            abort(403, message='No such user, or wrong password')
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


@blueprint.route('/register', endpoint='register')
class AuthRegisterAPI(MethodView):
    @blueprint.response(UserSchema)
    @blueprint.arguments(TokenSchema)
    def post(self, args):
        """Register new user"""
        email = args.get('email')
        password = args.get('password')
        try:
            User.get(email=args.get('email'))
            abort(409, message='User already registered')
        except User.DoesNotExist:
            user = User(email=email, password=hash_password(password))
        user.active = False
        user.save()
        return user
