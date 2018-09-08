from flask import Blueprint, render_template
from flask_restplus import Api
from flask_jwt_extended.exceptions import (
    CSRFError,
    NoAuthorizationError,
)
from jwt import ExpiredSignatureError


class ErrorFriendlyApi(Api):
    def error_router(self, original_handler, e):
        if type(e) in [
            CSRFError,
            ExpiredSignatureError,
            NoAuthorizationError,
        ]:
            return original_handler(e)
        else:
            return super(ErrorFriendlyApi, self).error_router(
                original_handler,
                e,
            )


api_v0 = Blueprint('api', __name__, url_prefix='/api/v0')

api = ErrorFriendlyApi(
    api_v0,
    version='0',
    title='API',
    description='API description',
    doc='/doc/',
    catch_all_404s=True,
    default='auth',
)
