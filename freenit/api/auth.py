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
            if current_app.dbtype == 'sql':
                user = User.get(email=email)
            else:
                user = User.objects.get(email=email)
        except User.DoesNotExist:
            abort(403, message='No such user, or wrong password')
        if not user or not user.active:
            abort(403, message='No such user, or wrong password')
        if not verify_password(password, user.password):
            abort(403, message='No such user, or wrong password')
        if current_app.dbtype == 'sql':
            id = user.id
        else:
            id = str(user.id)
        access_token = create_access_token(identity=id)
        refresh_token = create_refresh_token(identity=id)
        access_expire = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        refresh_expire = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        resp = jsonify(
            {
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
            if current_app.dbtype == 'sql':
                user = User.get(id=identity)
            else:
                user = User.objects.get(id=identity)
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
        email = args['email']
        password = args['password']
        User = current_app.user_datastore.user_model
        user = None
        try:
            User.get(email=email)
            abort(409, message='User already registered')
        except User.DoesNotExist:
            user = User(email=email, password=hash_password(password))
            user.save()
        expires = timedelta(
            hours=current_app.config['ACCOUNT_REQUEST_EXPIRY'],
        )
        identity = {
            'id': user.id,
            'request': True,
        }
        host = request.headers.get('Origin', request.url_root)
        requestToken = create_access_token(identity, expires_delta=expires)
        confirm = 'confirm'
        if host[-1] != '/':
            confirm = f'/{confirm}'
        url = f'{host}{confirm}/{requestToken}'
        msg = MIMEText(url, 'plain', 'utf-8')
        config = current_app.config
        subject = config['SUBJECTS']['prefix'] + config['SUBJECTS']['register']
        msg['To'] = user.email
        msg['From'] = config['FROM_EMAIL']
        msg['Subject'] = subject
        current_app.sendmail(msg)
        return user


@blueprint.route('/register/<token>', endpoint='register')
class AuthRegisterConfirmAPI(MethodView):
    @blueprint.response(UserSchema)
    def get(self, token):
        """Confirm new user"""
        decoded_token = decode_token(token)
        identity = decoded_token['identity']
        User = current_app.user_datastore.user_model
        user = None
        try:
            user = User.get(id=identity['id'])
        except User.DoesNotExist:
            abort(404, message='User does not exist')
        if user.active:
            abort(409, message='User already activated')
        user.active = True
        user.save()
        text = 'Congratulation, your account is confirmed'
        msg = MIMEText(text, 'plain', 'utf-8')
        config = current_app.config
        subject = config['SUBJECTS']['prefix'] + config['SUBJECTS']['confirm']
        msg['To'] = user.email
        msg['From'] = config['FROM_EMAIL']
        msg['Subject'] = subject
        current_app.sendmail(msg)
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
            subjects = current_app.config['SUBJECTS']
            subject = subjects['prefix'] + subjects['register']
            msg['Subject'] = subject
            msg['To'] = user.email
            current_app.sendmail(msg)
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
