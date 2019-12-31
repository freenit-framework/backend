from datetime import datetime, timedelta
from email.mime.text import MIMEText

from flask import current_app, jsonify, request
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt_identity,
    jwt_refresh_token_required,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies
)
from flask_security.utils import hash_password, verify_password
from flask_smorest import Blueprint, abort

from ..schemas.user import (
    LoginSchema,
    RefreshSchema,
    ResetSchema,
    TokenSchema,
    UserSchema
)

blueprint = Blueprint('auth', 'auth')


@blueprint.route('/login', endpoint='login')
class AuthLoginAPI(MethodView):
    @blueprint.response(LoginSchema)
    @blueprint.arguments(TokenSchema)
    def post(self, args):
        """Authenticates and generates a token"""
        email = args.get('email', None)
        password = args.get('password', None)
        if email is None:
            abort(403, message='Email not provided')
        User = current_app.user_datastore.user_model
        try:
            user = User.get(email=email)
        except User.DoesNotExist:
            abort(403, message='No such user, or wrong password')
        if not user or not user.active:
            abort(403, message='No such user, or wrong password')
        if not verify_password(password, user.password):
            abort(403, message='No such user, or wrong password')
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)
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


@blueprint.route('/logout', endpoint='logout')
class AuthLogoutAPI(MethodView):
    def post(self):
        """Logout"""
        resp = jsonify({})
        unset_jwt_cookies(resp)
        return resp


@blueprint.route('/refresh', endpoint='refresh')
class AuthRefreshAPI(MethodView):
    @blueprint.response(RefreshSchema)
    @jwt_refresh_token_required
    def post(self):
        """Refresh access token"""
        identity = get_jwt_identity()
        User = current_app.user_datastore.user_model
        try:
            user = User.get(id=identity)
        except User.DoesNotExist:
            abort(403, message='No such user, or wrong password')
        if not user.active:
            abort(403, message='No such user, or wrong password')
        access_expire = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        access_token = create_access_token(identity=identity)
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
        User = current_app.user_datastore.user_model
        try:
            User.get(email=args.get('email'))
            abort(409, message='User already registered')
        except User.DoesNotExist:
            user = User(email=email, password=hash_password(password))
        user.save()
        return user


@blueprint.route('/reset/request', endpoint='reset_request')
class AuthResetRequestAPI(MethodView):
    @blueprint.response(TokenSchema)
    @blueprint.arguments(TokenSchema(only=('email', )))
    def post(self, args):
        """Request user password reset"""
        User = current_app.user_datastore.user_model
        try:
            user = User.get(email=args['email'], active=True)
            expires = timedelta(
                hours=current_app.config['PASSWORD_RESET_EXPIRY'],
            )
            identity = {
                'id': user.id,
                'reset': True,
            }
            host = request.headers.get('Origin', request.url_root)
            resetToken = create_access_token(identity, expires_delta=expires)
            url = f'{host}/reset/{resetToken}'
            msg = MIMEText(url, 'plain', 'utf-8')
            msg['From'] = 'office@example.com'
            msg['Subject'] = 'Freenit message'
            to = ['meka@tilda.center']
            current_app.sendmail(to, msg)
        except User.DoesNotExist:
            pass
        return {}


@blueprint.route('/reset', endpoint='reset')
class AuthResetAPI(MethodView):
    @blueprint.response(ResetSchema)
    @blueprint.arguments(ResetSchema)
    def post(self, args):
        """Reset user password"""
        decoded_token = decode_token(args['token'])
        identity = decoded_token['identity']
        if not identity.get('reset', False):
            abort(409, message='Not reset token')
        User = current_app.user_datastore.user_model
        try:
            user = User.get(id=identity['id'], active=True)
        except User.DoesNotExist:
            abort(404, message='No such user')
        user.password = hash_password(args['password'])
        user.save()
        return {}
